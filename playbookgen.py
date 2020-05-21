import errno
import os

###################################################################################################
FOR_ALL = """---
- hosts: all
  become: true
  tasks:
    - name: Install aptitude using apt
      apt:
        name: aptitude
        state: latest
        update_cache: yes
        force_apt_get: yes
    - name: Install Docker's dependencies
      apt:
        name:
          - apt-transport-https
          - ca-certificates
          - gnupg-agent
          - software-properties-common
          - python3-pip
        update_cache: yes
        state: present
    - name: Add Docker's official GPG key
      apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present
    - name: Add Docker Repository
      apt_repository:
        repo: deb https://download.docker.com/linux/ubuntu bionic stable
        state: present
    - name: Install Docker
      apt:
        name: 
          - docker-ce
          - docker-ce-cli
          - containerd.io
        update_cache: yes
        state: present
    - name: Ensure group "docker" exists
      group:
        name: docker
        state: present
    - name: Add user "nexgus" into "docker" group
      user:
        name: nexgus
        groups: docker
        append: yes
    - name: Install Docker Compose
      get_url:
        url: https://github.com/docker/compose/releases/download/1.25.5/docker-compose-Linux-x86_64
        dest: /usr/local/bin/docker-compose
        mode: "0755"
    - name: Create symbolic link for Docker Compose
      file:
        src: /usr/local/bin/docker-compose
        dest: /usr/bin/docker-compose
        state: link
    - name: Upgrade PIP
      shell: python3 -m pip install -U pip
    - name: Install Python modules
      pip:
        name:
          - docker
          - docker-compose
        state: latest
    - name: Pull ZooKeeper Docker image
      docker_image:
        name: "nexgus/zookeeper:3.6.1"
        source: pull
    - name: Pull Kafka Docker image
      docker_image:
        name: "nexgus/kafka:2.12-2.4.1"
        source: pull
"""

###################################################################################################
def inventory(workdir, ip_list=[], user='nexgus', private_key='~/.ssh/id_rsa'):
    with open(os.path.join(workdir, 'ansible.cfg'), 'w') as fp:
        fp.write('[defaults]\n')
        fp.write('inventory=./hosts\n')
        fp.write('interpreter_python=auto\n') # Ensure run python3
        fp.write('host_key_checking=False\n') # Append remote to known_hosts automatically
        # if the remote ask sudo password, there are two options you may use:
        #   1. ansible-playbook deploy.yml --extra-vars "ansible_sudo_pass=0000"
        #   2. ansible-playbook deploy.yml --ask-become-pass
        # Option 2 needs to enter password manually.

    with open(os.path.join(workdir, 'hosts'), 'w') as fp:
        for idx, ip in enumerate(ip_list):
            fp.write(f'[server{idx+1}]\n')
            fp.write(f'{ip} ansible_ssh_user={user} ansible_ssh_private_key_file={private_key}\n')
            fp.write( '\n')

###################################################################################################
def playbook(filepath, 
             host_ip=[], 
             private_ip=[], 
             public_ip=[], 
             kafka_volume='kafka', 
             zookeeper_volume='zookeeper', 
             mount=None):
    with open(filepath, 'w') as fp:
        fp.write(FOR_ALL)

        if mount:
            device, mount_point = mount.split(':')
            fp.write( '    - name: Install partition tool "parted"\n')
            fp.write( '      apt:\n')
            fp.write( '        name: parted\n')
            fp.write( '        state: present\n')
            fp.write( '    - name: Create partition for data disk\n')
            fp.write( '      parted:\n')
            fp.write(f'        device: {device}\n')
            fp.write( '        number: 1\n')
            fp.write( '        state: present\n')
            fp.write( '    - name: Format data disk\n')
            fp.write( '      filesystem:\n')
            fp.write(f'        device: {device}1\n')
            fp.write( '        force: yes\n')
            fp.write( '        fstype: ext4\n')
            fp.write( '    - name: Create a mount point for data disk\n')
            fp.write( '      file:\n')
            fp.write(f'        path: {mount_point}\n')
            fp.write( '        state: directory\n')
            fp.write( '    - name: Mount data disk\n')
            fp.write( '      mount:\n')
            fp.write(f'        path: {mount_point}\n')
            fp.write(f'        src: {device}1\n')
            fp.write( '        fstype: ext4\n')
            fp.write( '        state: mounted\n')
            fp.write( '    - name: Create data directory for ZooKeeper\n')
            fp.write( '      file:\n')
            fp.write(f'        path: {mount_point}/zookeeper\n')
            fp.write( '        state: directory\n')
            fp.write( '    - name: Create data directory for Kafka\n')
            fp.write( '      file:\n')
            fp.write(f'        path: {mount_point}/kafka\n')
            fp.write( '        state: directory\n')
        fp.write('\n')

        for idx, host in enumerate(host_ip):
            fp.write(f'- hosts: server{idx+1}\n')
            fp.write( '  become: true\n')
            fp.write( '  tasks:\n')
            fp.write( '    - name: Run ZooKeeper and Kafka\n')
            fp.write( '      docker_compose:\n')
            fp.write( '        project_name: nexcom\n')
            fp.write( '        definition:\n')
            fp.write( '          version: "2"\n')

            # Ansible service definition for ZooKeeper
            fp.write( '          services:\n')
            fp.write( '            zookeeper:\n')
            fp.write( '              image: "nexgus/zookeeper:3.6.1"\n')
            fp.write( '              ports:\n')
            fp.write( '                - "2181:2181"\n')
            fp.write( '                - "2888:2888"\n')
            fp.write( '                - "3888:3888"\n')
            fp.write( '              volumes:\n')
            fp.write(f'                - "{zookeeper_volume}:/var/lib/zookeeper"\n')
            fp.write( '              environment:\n')
            fp.write(f'                ZK_ID: "{idx+1}"\n')
            fp.write( '                ZK_dataDir: "/var/lib/zookeeper"\n')
            for server, ip in enumerate(private_ip):
                fp.write(f'                ZK_server_{server+1}: "{ip}:2888:3888"\n')
            fp.write( '              restart: unless-stopped\n')

            # Ansible service definition for Kafka
            fp.write( '            kafka:\n')
            fp.write( '              image: "nexgus/kafka:2.12-2.4.1"\n')
            fp.write( '              ports:\n')
            fp.write( '                - "9092:9092"\n')
            fp.write( '                - "9094:9094"\n')
            fp.write( '              volumes:\n')
            fp.write(f'                - "{kafka_volume}:/var/lib/kafka"\n')
            fp.write( '              environment:\n')
            fp.write(f'                KK_BROKER_ID: "{idx}"\n')
            fp.write( '                KK_LOG_DIR: "/var/lib/kafka"\n')
            fp.write( '                KK_LISTENERS: "INTRANET://0.0.0.0:9094,INTERNET://0.0.0.0:9092"\n')
            fp.write(f'                KK_ADVERTISED_LISTENERS: "INTRANET://{private_ip[idx]}:9094,INTERNET://{public_ip[idx]}:9092"\n')
            fp.write( '                KK_LISTENER_SECURITY_PROTOCOL_MAP: "INTRANET:PLAINTEXT,INTERNET:PLAINTEXT"\n')
            fp.write( '                KK_INTER_BROKER_LISTENER_NAME: "INTRANET"\n')
            KK_ZOOKEEPER_CONNECT = 'KK_ZOOKEEPER_CONNECT: "' + ','.join([f'{ip}:2181' for ip in private_ip]) + '"'
            fp.write(f'                {KK_ZOOKEEPER_CONNECT}\n')
            fp.write( '              restart: unless-stopped\n')
            fp.write( '\n')

            # Ansible Volume Definition
            if (not zookeeper_volume.startswith('/')) or (not kafka_volume.startswith('/')):
                fp.write( '          volumes:\n')
                if not zookeeper_volume.startswith('/'):
                    fp.write(f'            {zookeeper_volume}:\n')
                    fp.write(f'              driver: local\n')
                if not kafka_volume.startswith('/'):
                    fp.write(f'            {kafka_volume}:\n')
                    fp.write(f'              driver: local\n')

###################################################################################################
def main(args):
    host_ip = args.public_ip
    os.makedirs(args.workdir, exist_ok=True)

    inventory(
        workdir=args.workdir,
        ip_list=host_ip,
        user=args.user,
        private_key=args.key,
    )

    playbook(
        os.path.join(args.workdir, 'deploy.yml'),
        host_ip=host_ip, 
        private_ip=args.private_ip, 
        public_ip=([] if args.public_ip is None else args.public_ip),
        kafka_volume=args.kafka_volume,
        zookeeper_volume=args.zookeeper_volume,
        mount=args.mount,
    )

###################################################################################################
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Ansible Playbook Generator for Kafka Cluster.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--private-ip',
                        nargs='+',
                        type=str,
                        help='Kafka inter-server IPs/hostnames.')
    parser.add_argument('-a', '--public-ip',
                        nargs='+',
                        type=str,
                        help='Kafka advised IPs/hostnames.')
    parser.add_argument('-w', '--workdir',
                        type=str,
                        default='./playbooks',
                        help='Generated playbook directory.')
    parser.add_argument('-u', '--user',
                        type=str,
                        default=os.environ['USER'],
                        help='SSH user name.')
    parser.add_argument('-k', '--key',
                        type=str,
                        default='~/.ssh/id_rsa',
                        help='Path to SSH private key.')
    parser.add_argument('-zv', '--zookeeper-volume',
                        type=str,
                        default='zookeeper',
                        help='ZooKeeper volume or path to host machine.')
    parser.add_argument('-kv', '--kafka-volume',
                        type=str,
                        default='kafka',
                        help='Kafka volume or path to host machine.')
    parser.add_argument('-m', '--mount',
                        type=str,
                        help='Data disk mount info in format "<device>:<mount point>".'
                             'If --mount is set, --zookeeper-volume and --kafka-volume '
                             'will be set automatically.')
    args = parser.parse_args()

    args.key = os.path.expanduser(args.key)
    if not os.path.isfile(args.key):
        raise OSError(
            errno.ENOENT,
            'No such file or directory',
            args.key)

    if os.path.isfile(args.workdir):
        raise OSError(
            errno.EEXIST,
            'File exists',
            args.workdir)

    if args.private_ip is None:
        args.private_ip = ['localhost']

    if args.public_ip is None:
        args.public_ip = args.private_ip
    else:
        if len(args.public_ip) != len(args.private_ip):
            raise ValueError('Public IP count ({len(args.public_ip)}) must '
                             'equal to private IP count ({len(args.provate_ip)})')

    if args.mount:
        mount_point = args.mount.split(':')[-1]
        args.zookeeper_volume = os.path.join(mount_point, 'zookeeper')
        args.kafka_volume = os.path.join(mount_point, 'kafka')

    main(args)

# https://docs.microsoft.com/en-us/samples/azure-samples/virtual-machines-python-manage/azure-virtual-machines-management-samples---python/
# https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal#get-application-id-and-authentication-key
# Display name: DeployKafkaVM
# Application (client) ID: 1051f293-c5a6-4813-8f7d-e7d7f2f04749
# Directory (tenant) ID:   150ede72-6bf3-4029-ac57-de982587a01e
# Object ID:               0e4d7156-d8fb-462e-a703-b17b0f6ecb6b
