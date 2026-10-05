"""
FaceCam AI Processor for Recplay Studio 2.0
Provides high-performance Background Blur and Body/Face Cutout ("No square, No round, Only show body").
Powered by MediaPipe Neural Selfie Segmentation with temporal EMA smoothing and OpenCV YuNet face detection.
"""

import os
import sys
from pathlib import Path
import cv2
import numpy as np


class FaceCamProcessor:
    """
    AI Face & Body Portrait Processor for Webcam Facecam:
    - Mode 'blur': DSLR Studio Bokeh Background Blur (keeps speaker body sharp, deeply blurs room/office).
    - Mode 'face_only': Seamless Body Cutout (zero square and zero round frame, zero background, only body floats on screen).
    - Mode 'standard': Normal camera pass-through.
    """

    def __init__(self, model_path: str | None = None, seg_model_path: str | None = None):
        self.segmenter = None
        self.detector = None
        self.last_seg_mask = None
        self.last_face = None  # (fx, fy, fw, fh) smoothed
        self.frames_since_detect = 0
        self.smooth_alpha = 0.35  # Exponential moving average factor
        self.smoothed_body_bbox = None  # (y1, y2, x1, x2) smoothed crop box

        # 1. Load Neural Selfie Segmentation Model (MediaPipe ONNX)
        if seg_model_path is None:
            seg_candidates = [
                Path(__file__).resolve().parent.parent / "assets" / "models" / "selfie_segmentation.onnx",
                Path(__file__).resolve().parent / "assets" / "models" / "selfie_segmentation.onnx",
                Path("D:/Clipr/2.0/assets/models/selfie_segmentation.onnx"),
                Path("D:/ScreenRecorderPro/assets/models/selfie_segmentation.onnx"),
            ]
            for p in seg_candidates:
                if p.exists():
                    seg_model_path = str(p)
                    break

        if seg_model_path and os.path.exists(seg_model_path):
            try:
                self.segmenter = cv2.dnn.readNetFromONNX(seg_model_path)
            except Exception as e:
                print(f"[FaceCamProcessor] Warning: Could not initialize Selfie Segmentation ({e}).")
                self.segmenter = None

        # 2. Load Auxiliary Face Detector (OpenCV YuNet ONNX) as fallback
        if model_path is None:
            candidates = [
                Path(__file__).resolve().parent.parent / "assets" / "models" / "face_detection_yunet.onnx",
                Path(__file__).resolve().parent / "assets" / "models" / "face_detection_yunet.onnx",
                Path("D:/Clipr/2.0/assets/models/face_detection_yunet.onnx"),
                Path("D:/ScreenRecorderPro/assets/models/face_detection_yunet.onnx"),
            ]
            for p in candidates:
                if p.exists():
                    model_path = str(p)
                    break

        if model_path and os.path.exists(model_path):
            try:
                self.detector = cv2.FaceDetectorYN.create(
                    model_path,
                    "",
                    (320, 240),
                    score_threshold=0.55,
                    nms_threshold=0.3,
                    top_k=5,
                )
            except Exception:
                self.detector = None

    def segment_person(self, bgr_frame: np.ndarray) -> np.ndarray:
        """
        Extracts pixel-level probability mask of the person's body (hair, face, neck, shoulders, torso).
        Returns a float32 mask of shape (h, w) in range [0.0, 1.0], where
        1.0 = human body, 0.0 = background (room, walls, chair, etc.).
        """
        if bgr_frame is None:
            return np.zeros((240, 320), dtype=np.float32)

        h, w = bgr_frame.shape[:2]

        if self.segmenter is not None:
            try:
                # Pre-process into 256x256 RGB normalized blob
                blob = cv2.dnn.blobFromImage(
                    bgr_frame,
                    scalefactor=1.0 / 255.0,
                    size=(256, 256),
                    swapRB=True,
                )
                self.segmenter.setInput(blob)
                raw_out = self.segmenter.forward()

                # Handle all ONNX output tensor layouts:
                # [1, 2, 256, 256], [1, 256, 256, 2], [1, 1, 256, 256], or [1, 256, 256, 1]
                if raw_out.ndim == 4:
                    if raw_out.shape[1] == 2:
                        bg_ch = raw_out[0, 0]
                        fg_ch = raw_out[0, 1]
                        max_c = np.maximum(bg_ch, fg_ch)
                        exp_bg = np.exp(bg_ch - max_c)
                        exp_fg = np.exp(fg_ch - max_c)
                        mask_2d = exp_fg / (exp_bg + exp_fg + 1e-7)
                    elif raw_out.shape[3] == 2:
                        bg_ch = raw_out[0, :, :, 0]
                        fg_ch = raw_out[0, :, :, 1]
                        max_c = np.maximum(bg_ch, fg_ch)
                        exp_bg = np.exp(bg_ch - max_c)
                        exp_fg = np.exp(fg_ch - max_c)
                        mask_2d = exp_fg / (exp_bg + exp_fg + 1e-7)
                    elif raw_out.shape[1] == 1:
                        mask_2d = raw_out[0, 0]
                    elif raw_out.shape[3] == 1:
                        mask_2d = raw_out[0, :, :, 0]
                    else:
                        mask_2d = raw_out[0, -1]
                elif raw_out.ndim == 3:
                    mask_2d = raw_out[0]
                else:
                    mask_2d = raw_out.squeeze()

                # Normalize to [0.0, 1.0] if raw logits
                if np.nanmax(mask_2d) > 1.0 or np.nanmin(mask_2d) < 0.0:
                    mask_2d = 1.0 / (1.0 + np.exp(-np.clip(mask_2d, -15.0, 15.0)))

                # Polarity auto-detection: background corners vs presenter center
                mh, mw = mask_2d.shape[:2]
                corners = [mask_2d[0, 0], mask_2d[0, -1], mask_2d[-1, 0], mask_2d[-1, -1]]
                center_val = mask_2d[mh // 2, mw // 2]
                if np.mean(corners) > center_val and center_val < 0.45:
                    mask_2d = 1.0 - mask_2d

                prob_mask = cv2.resize(mask_2d.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)

                # Temporal exponential smoothing to prevent edge flicker
                if self.last_seg_mask is not None and self.last_seg_mask.shape == (h, w):
                    prob_mask = 0.72 * prob_mask + 0.28 * self.last_seg_mask
                self.last_seg_mask = prob_mask.copy()

                # Smooth contrast S-curve for crisp, natural edges around hair & clothes
                soft_mask = np.clip((prob_mask - 0.22) / 0.52, 0.0, 1.0)
                soft_mask = cv2.GaussianBlur(soft_mask, (7, 7), 0)
                return soft_mask.astype(np.float32)
            except Exception:
                pass

        # Fallback: synthesize portrait mask from face detection or centered upper body
        face = self.detect_face(bgr_frame)
        mask = np.zeros((h, w), dtype=np.float32)
        if face is not None:
            fx, fy, fw, fh = face
            cx = int(fx + fw * 0.5)
            cy = int(fy + fh * 0.50)
            rx, ry = int(fw * 0.72), int(fh * 0.85)
            cv2.ellipse(mask, (cx, cy), (rx, ry), 0, 0, 360, 1.0, -1)
            torso_cy = int(cy + fh * 1.0)
            torso_rx, torso_ry = int(fw * 1.45), int(fh * 1.05)
            cv2.ellipse(mask, (cx, torso_cy), (torso_rx, torso_ry), 0, 0, 360, 1.0, -1)
        else:
            cv2.ellipse(mask, (w // 2, int(h * 0.42)), (int(w * 0.36), int(h * 0.46)), 0, 0, 360, 1.0, -1)

        mask = cv2.GaussianBlur(mask, (35, 35), 0)
        return mask

    def detect_face(self, bgr_frame: np.ndarray) -> tuple[int, int, int, int] | None:
        """
        Detects primary presenter face with temporal smoothing.
        Returns (fx, fy, fw, fh) in pixel coordinates of bgr_frame.
        """
        if bgr_frame is None:
            return self.last_face

        h, w = bgr_frame.shape[:2]

        if self.detector is not None:
            try:
                self.detector.setInputSize((w, h))
                ret, faces = self.detector.detect(bgr_frame)
                if ret and faces is not None and len(faces) > 0:
                    best_face = max(faces, key=lambda f: float(f[2] * f[3]))
                    raw_fx, raw_fy, raw_fw, raw_fh = (
                        float(best_face[0]),
                        float(best_face[1]),
                        float(best_face[2]),
                        float(best_face[3]),
                    )

                    if self.last_face is not None:
                        s_fx = self.smooth_alpha * raw_fx + (1.0 - self.smooth_alpha) * self.last_face[0]
                        s_fy = self.smooth_alpha * raw_fy + (1.0 - self.smooth_alpha) * self.last_face[1]
                        s_fw = self.smooth_alpha * raw_fw + (1.0 - self.smooth_alpha) * self.last_face[2]
                        s_fh = self.smooth_alpha * raw_fh + (1.0 - self.smooth_alpha) * self.last_face[3]
                        self.last_face = (int(s_fx), int(s_fy), int(s_fw), int(s_fh))
                    else:
                        self.last_face = (int(raw_fx), int(raw_fy), int(raw_fw), int(raw_fh))

                    self.frames_since_detect = 0
                    return self.last_face
            except Exception:
                pass

        self.frames_since_detect += 1
        if self.last_face is not None and self.frames_since_detect < 25:
            return self.last_face

        cw, ch = int(w * 0.45), int(h * 0.55)
        cx, cy = (w - cw) // 2, int(h * 0.2)
        return (cx, cy, cw, ch)

    def apply_background_blur(self, cam_frame: np.ndarray, blur_ksize: int = 51) -> np.ndarray:
        """
        True DSLR Studio Portrait Bokeh Background Blur:
        Preserves 100% of the presenter's body with razor-sharp original camera pixels
        while deeply blurring the room background with creamy bokeh.
        """
        if cam_frame is None:
            return cam_frame

        h, w = cam_frame.shape[:2]
        mask = self.segment_person(cam_frame)  # Float32 [0.0, 1.0]

        # Multi-scale creamy DSLR bokeh without pixelation
        dw, dh = max(32, w // 2), max(24, h // 2)
        small = cv2.resize(cam_frame, (dw, dh), interpolation=cv2.INTER_LINEAR)
        small = cv2.GaussianBlur(small, (35, 35), 0)
        small = cv2.GaussianBlur(small, (25, 25), 0)
        blurred_bg = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)

        # 3-channel alpha mask with smooth transition
        mask_3ch = np.dstack([mask, mask, mask])

        # Composite: sharp original camera frame where person is, smooth bokeh background
        composite = (cam_frame.astype(np.float32) * mask_3ch + blurred_bg.astype(np.float32) * (1.0 - mask_3ch))
        return np.clip(composite, 0, 255).astype(np.uint8)

    def apply_face_cutout(
        self, cam_frame: np.ndarray, target_size: int = 280
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        High-Quality Body & Face Cutout ("No square, No round, Only show exact body"):
        Preserves the exact camera image quality with crystal clarity and zero background.
        Returns:
            resized_body: (nh, nw, 3) BGR image
            alpha_3ch: (nh, nw, 3) float32 mask with values [0.0, 1.0]
        """
        if cam_frame is None:
            dummy = np.zeros((target_size, target_size, 3), dtype=np.uint8)
            return dummy, np.zeros((target_size, target_size, 3), dtype=np.float32)

        h, w = cam_frame.shape[:2]
        mask = self.segment_person(cam_frame)

        # Detect the bounding bounds of the presenter's body with stability smoothing
        ys, xs = np.where(mask > 0.18)
        if len(ys) > 300:
            pad_y = 20
            pad_x = 24
            raw_y1, raw_y2 = max(0, int(np.min(ys) - pad_y)), min(h, int(np.max(ys) + pad_y))
            raw_x1, raw_x2 = max(0, int(np.min(xs) - pad_x)), min(w, int(np.max(xs) + pad_x))

            # Apply temporal smoothing to bounding box to eliminate jitter
            if self.smoothed_body_bbox is not None:
                sm = 0.20
                sy1 = int(sm * raw_y1 + (1.0 - sm) * self.smoothed_body_bbox[0])
                sy2 = int(sm * raw_y2 + (1.0 - sm) * self.smoothed_body_bbox[1])
                sx1 = int(sm * raw_x1 + (1.0 - sm) * self.smoothed_body_bbox[2])
                sx2 = int(sm * raw_x2 + (1.0 - sm) * self.smoothed_body_bbox[3])
                self.smoothed_body_bbox = (sy1, sy2, sx1, sx2)
            else:
                self.smoothed_body_bbox = (raw_y1, raw_y2, raw_x1, raw_x2)

            y1, y2, x1, x2 = self.smoothed_body_bbox
        else:
            y1, y2 = 0, h
            x1, x2 = 0, w

        body_crop = cam_frame[y1:y2, x1:x2]
        mask_crop = mask[y1:y2, x1:x2]
        ch, cw = body_crop.shape[:2]

        if ch <= 0 or cw <= 0:
            body_crop = cam_frame
            mask_crop = mask
            ch, cw = h, w

        # Maintain exact aspect ratio and use high-fidelity Lanczos/Cubic interpolation
        scale = float(target_size) / max(ch, cw, 1)
        nw, nh = max(48, int(cw * scale)), max(48, int(ch * scale))

        interp = cv2.INTER_LANCZOS4 if scale > 0.8 else cv2.INTER_AREA
        resized_body = cv2.resize(body_crop, (nw, nh), interpolation=interp)
        resized_mask = cv2.resize(mask_crop, (nw, nh), interpolation=cv2.INTER_LINEAR)

        # Soft bottom edge fade so the body rests naturally on the screen border
        fade_len = min(28, max(8, nh // 8))
        if fade_len > 0:
            bottom_fade = np.ones((nh, nw), dtype=np.float32)
            for r in range(fade_len):
                bottom_fade[nh - 1 - r, :] = float(r) / float(fade_len)
            resized_mask = resized_mask * bottom_fade

        alpha_3ch = np.dstack([resized_mask, resized_mask, resized_mask])
        return resized_body, alpha_3ch
