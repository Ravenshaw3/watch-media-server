# SSH to Unraid server with key authentication
# Usage: .\scripts\ssh-unraid.ps1 [command]

param(
    [string]$Command = ""
)

$unraidIP = "192.168.254.14"
$sshKey = "$env:USERPROFILE\.ssh\unraid_key"

if ($Command) {
    # Execute command remotely
    ssh -i $sshKey root@$unraidIP $Command
} else {
    # Start interactive SSH session
    ssh -i $sshKey root@$unraidIP
}
