from subprocess import Popen, PIPE
import socket
import os

class RunCMD:

    """
     -- RunCMD class -- run shell commands on the local machine or remote through ssh

        through ssh example:
            cmd = RunCMD(ssh_host="my-srv.example.local",ssh_user="myuser",ssh_key="~/.ssh/id_rsa",ssh_port=22)

            # add the host server fingerprint to the known_hosts file but do not override if exists mismatch
            cmd.add_figerprint(override_fp=False)

            # override the host server fingerprint if exists and mismatch
            cmd.add_figerprint(override_fp=True)

        local run cmd example:
            cmd = RunCMD()

        cmd.shell("ls -lh")
    """

    def __init__(self,ssh_host:str=None,ssh_user:str=None,ssh_key:str="~/.ssh/id_rsa",ssh_port:str="22",ssh_known_hosts:str="~/.ssh/known_hosts",timeout:int=2):
        self.ssh_host=ssh_host
        self.ssh_user=ssh_user
        self.ssh_key=os.path.expanduser(ssh_key)
        self.ssh_port=ssh_port
        self.timeout=timeout
        self.fingerprint_file=os.path.expanduser(ssh_known_hosts)

    # check if the host is up
    def is_host_up(self,timeout:int=2) -> bool:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")

        try:
            socket.create_connection((self.ssh_host,self.ssh_port),timeout=timeout)
            return True
        except:
            return False

    # run shell command
    def run_cmd(self,cmd:str,stdinput:str=None) -> tuple:
        try:
            if(stdinput):
                rp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE,input=stdinput.encode())
            else:
                rp = Popen(cmd,shell=True,stdout=PIPE,stderr=PIPE)
            stdout,stderr = rp.communicate()
            if(rp.returncode == 0):
                if(stdout):
                    return ('stdout', stdout.decode('UTF-8'))
                return ('stdout','OK')
            if(stderr):
                return ('stderr', stderr.decode('UTF-8'))
            return None
        except:
            return ('stderr', f"Error: Unable to run CMD: {cmd}")

    # get ssh server fingerprint
    def get_server_fingerprint(self) -> list:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")
        
        cmd = f"ssh-keyscan -p {self.ssh_port} {self.ssh_host} 2>/dev/null"
        data = self.run_cmd(cmd)
        fp_list = []
        if(data and 'stdout' in data):
            for line in data[1].split("\n"):
                if(line):
                    fp_list.append(line)
        return fp_list

    # get local known_hosts file fingerprint
    def get_local_fingerprint(self) -> list:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")

        if(not os.path.isfile(self.fingerprint_file)):
            return None
        
        fp_local_list = []
        with open(self.fingerprint_file,'r') as file:
            for line in file:
                if(self.ssh_host in line):
                    fp_local_list.append(line.strip())
        return fp_local_list

    def check_fingerprint(self) -> bool:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")

        fp_server = self.get_server_fingerprint()
        fp_local = self.get_local_fingerprint()

        if(fp_server and fp_local):
            if not set(fp_server).issubset(set(fp_local)):
                raise Exception(f"Host {self.ssh_host} fingerprint mismatch")
            return True

        return False
    
    # delete fingerprint from known_hosts file
    def delete_fingerprint(self) -> bool:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")
        
        try:
            self.check_fingerprint()
        except Exception as e:
            #print(e)
            with open(self.fingerprint_file,'r') as file:
                lines = file.readlines()
            with open(self.fingerprint_file,'w') as file:
                for line in lines:
                    if(self.ssh_host not in line):
                        file.write(line)
            return True
        return False

    # add fingerprint to local known_hosts file
    def add_figerprint(self,override_fp=False) -> bool:

        if(not self.ssh_host):
            raise Exception("No ssh host defined")
        
        if(override_fp):
            self.delete_fingerprint()
        
        try:
            fp_state = self.check_fingerprint()
        except Exception as e:
            #print(e)
            return False

        if(not fp_state):
            fp_list = self.get_server_fingerprint()
            with open(self.fingerprint_file,'a') as file:
                for line in fp_list:
                    file.write(line + "\n")
        return True

    # run shell command on local machine or remote through ssh
    def shell(self,cmd:str) -> tuple:
        """
        Run a shell command on the local machine or remote through ssh
        retrun: tuple (stdout|stderr, output)
        """
        if(self.ssh_host):

            if(not self.is_host_up(self.timeout)):
                return ('stderr', f'Host {self.ssh_host} is down')

            if(not self.ssh_user):
                return ('stderr', 'SSH User not defined')

            if(not os.path.isfile(self.ssh_key)):
                return ('stderr', f'SSH Key {self.ssh_key} not found')

            try:
                if(not self.check_fingerprint()):
                    return ('stderr', f'Theres no figerprint for {self.ssh_host} in known_hosts file')
                cmd = f'ssh -i {self.ssh_key} -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} {cmd}'
            except Exception as e:
                return ('stderr', e)

        return self.run_cmd(cmd)