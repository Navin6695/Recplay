using System;
using System.IO;
using System.Diagnostics;
using System.Windows.Forms;

namespace RecplayKeygen
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string[] candidates = new string[]
                {
                    Path.Combine(baseDir, "Recplay.exe"),
                    Path.Combine(baseDir, "_internal", "Recplay.exe"),
                    Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Recplay", "Recplay.exe"),
                    @"D:\Clipr\2.0\dist\Recplay\Recplay.exe",
                    @"D:\Clipr\Recplay.exe"
                };

                string targetExe = null;
                foreach (var c in candidates)
                {
                    if (File.Exists(c))
                    {
                        targetExe = c;
                        break;
                    }
                }

                if (targetExe == null)
                {
                    MessageBox.Show(
                        "Could not locate Recplay.exe to launch Keygen.\n\nPlease install Recplay 2.0 or place Recplay_Keygen.exe in the Recplay application folder.",
                        "Recplay Keygen",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = targetExe;
                string extraArgs = (args != null && args.Length > 0) ? (" " + string.Join(" ", args)) : "";
                psi.Arguments = "--keygen" + extraArgs;
                psi.WorkingDirectory = Path.GetDirectoryName(targetExe);
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;

                Process.Start(psi);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error starting Recplay Keygen: " + ex.Message, "Recplay Keygen", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
