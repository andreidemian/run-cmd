from subprocess import Popen, PIPE
import hashlib
import socket
import os

class RunCMD:

    """
     -- RunCMD class -- run shell commands on the local machine or remote through ssh

        through ssh example:
            cmd = RunCMD(ssh_host="my-srv.example.local",ssh_user="myuser",ssh_key="~/.ssh/id_rsa",ssh_port=22)
        
        local run cmd example:
            cmd = RunCMD()

        cmd.shell("ls -lh")
    """

    def __init__(self,ssh_host:str=None,ssh_user:str=None,ssh_key:str="~/.ssh/id_rsa",ssh_port:str="22",ssh_known_hosts:str="~/.ssh/known_hosts",accept_host_key:bool=False,timeout:int=2):
        self.ssh_host=ssh_host
        self.ssh_user=ssh_user
        self.ssh_key=os.path.expanduser(ssh_key)
        self.ssh_port=ssh_port
        self.accept_host_key=accept_host_key
        self.timeout=timeout
        self.fingerprint_file=os.path.expanduser(ssh_known_hosts)

    def is_host_up(self,timeout:int=2) -> bool:
        try:
            socket.create_connection((self.ssh_host,self.ssh_port),timeout=timeout)
            return True
        except:
            return False

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

    def get_server_fingerprint(self) -> list:
        cmd = f"ssh-keyscan -p {self.ssh_port} {self.ssh_host} 2>/dev/null"
        data = self.run_cmd(cmd)
        fp_list = []
        if(data and 'stdout' in data):
            for line in data[1].split("\n"):
                if(line):
                    fp_list.append(line)
        return fp_list

    def get_local_fingerprint(self) -> list:

        if(not os.path.isfile(self.fingerprint_file)):
            return None
        
        fp_local_list = []
        with open(self.fingerprint_file,'r') as file:
            for line in file:
                if(self.ssh_host in line):
                    fp_local_list.append(line.strip())
        return fp_local_list

    def check_fingerprint(self) -> bool:
        fp_server = self.get_server_fingerprint()
        fp_local = self.get_local_fingerprint()

        if(fp_server and fp_local):
            if not set(fp_server).issubset(set(fp_local)):
                raise Exception(f"Host {self.ssh_host} fingerprint mismatch")
            return True

        return False
    
    def delete_fingerprint(self) -> bool:
        try:
            self.check_fingerprint()
        except Exception as e:
            print(e)
            with open(self.fingerprint_file,'r') as file:
                lines = file.readlines()
            with open(self.fingerprint_file,'w') as file:
                for line in lines:
                    if(self.ssh_host not in line):
                        file.write(line)
            return True
        return False
        

    def add_figerprint(self,override_fp=False) -> bool:

        if(override_fp):
            self.delete_fingerprint()
        
        try:
            fp_state = self.check_fingerprint()
        except Exception as e:
            print(e)
            return False

        if(not fp_state):
            fp_list = self.get_server_fingerprint()
            with open(self.fingerprint_file,'a') as file:
                for line in fp_list:
                    file.write(line + "\n")
        return True

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

            if(self.accept_host_key):
                ssh_cmd = f'ssh -o StrictHostKeyChecking=no -i {self.ssh_key} -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} {cmd}'
                return self.run_cmd(ssh_cmd)

            figerprint = self.add_figerprint(self.ssh_host,int(self.ssh_port))
            if(figerprint):
                return ('stderr', f'Unable to add host {self.ssh_host} to known_hosts file')
            ssh_cmd = f'ssh -i {self.ssh_key} -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} {cmd}'


        return self.run_cmd(cmd)