use std::process::Command;

pub struct Sandbox;

impl Sandbox {
    pub fn run(command: &str) -> String {
        // Simple Docker wrapper: run in a temporary alpine container
        // We'll use 'sh -c' to support piping/redirection if needed
        let output = Command::new("docker")
            .arg("run")
            .arg("--rm")
            .arg("alpine")
            .arg("sh")
            .arg("-c")
            .arg(command)
            .output();

        match output {
            Ok(out) => {
                let stdout = String::from_utf8_lossy(&out.stdout).to_string();
                let stderr = String::from_utf8_lossy(&out.stderr).to_string();
                if out.status.success() {
                    stdout
                } else {
                    format!("Error: {}", stderr)
                }
            }
            Err(e) => format!("Failed to execute docker: {}", e),
        }
    }
}
