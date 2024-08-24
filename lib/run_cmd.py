from subprocess import Popen, PIPE
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

    def __init__(self,ssh_host:str=None,ssh_user:str=None,ssh_key:str="~/.ssh/id_rsa",ssh_port:str="22",accept_host_key:bool=True,timeout:int=2):
        self.ssh_host=ssh_host
        self.ssh_user=ssh_user
        self.ssh_key=os.path.expanduser(ssh_key)
        self.ssh_port=ssh_port
        self.accept_host_key=accept_host_key
        self.timeout=timeout

    def is_host_up(self,timeout:int=2) -> bool:
        try:
            socket.create_connection((self.ssh_host,self.ssh_port),timeout=timeout)
            return True
        except:
            return False

    def run_cmd(self,cmd:str) -> str:
        try:
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

    def shell(self,cmd:str) -> str:

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

            ssh_cmd = f'ssh -i {self.ssh_key} -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} {cmd}'
            if(self.accept_host_key):
                ssh_cmd = f'ssh -o StrictHostKeyChecking=no -i {self.ssh_key} -p {self.ssh_port} {self.ssh_user}@{self.ssh_host} {cmd}'
            return self.run_cmd(ssh_cmd)

        return self.run_cmd(cmd)


        