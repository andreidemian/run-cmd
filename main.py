from lib.run_cmd import RunCMD

# create an instance of the RunCMD class to run commands on the local machine
#cmd = RunCMD()

# create and instance of the RunCMD class to run commands on a remote machine
cmd = RunCMD(ssh_host="192.168.111.132",ssh_user="root",ssh_key="~/.ssh/id_rsa",ssh_port=22)

# add the host server fingerprint to the known_hosts file
cmd.add_figerprint()

# run command on the local machine
returned_data = cmd.shell("ip -br addr")

# check if the command was successful
if(returned_data is not None and returned_data[0] == 'stdout'):
    print(f"Output: {returned_data[1]}")

# check if the command failed
if(returned_data is not None and returned_data[0] == 'stderr'):
    print(f"Error: {returned_data[1]}")
