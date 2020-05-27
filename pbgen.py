#/usr/bin/env python3
# -*- coding: utf-8 -*-
import errno
import os
import sys

###############################################################################
def inventory(workdir, ip_list=[], user='nexgus', private_key='~/.ssh/id_rsa'):
    stdout = sys.stdout

    with open(os.path.join(workdir, 'ansible.cfg'), 'w') as fp:
        sys.stdout = fp
        print('[defaults]')
        print('inventory=./hosts')
        print('interpreter_python=auto')
        print('host_key_checking=False')
        # if the remote ask sudo password, there are two options you may use:
        # ansible-playbook deploy.yml --extra-vars "ansible_sudo_pass=0000"
        # or
        # ansible-playbook deploy.yml --ask-become-pass
        # Option 2 needs to enter password manually.

    with open(os.path.join(workdir, 'hosts'), 'w') as fp:
        sys.stdout = fp
        for idx, ip in enumerate(ip_list):
            print(f'[server{idx+1}]')
            print(f'{ip} '
                  f'ansible_ssh_user={user} '
                  f'ansible_ssh_private_key_file={private_key}')

    sys.stdout = stdout

###############################################################################
def playbook(filepath, 
             host_ip=[], 
             private_ip=[], 
             public_ip=[], 
             username='deployer',
             zookeeper_volume='zookeeper', 
             kafka_volume='kafka', 
             kafka_retention_hours=168, 
             kafka_retention_bytes=-1, 
             mount=None):
    stdout = sys.stdout

    with open(filepath, 'w') as fp:
        sys.stdout = fp

        print( '---')
        print( '- hosts: all')
        print( '  become: true')
        print( '  tasks:')
        print( '  - name: Install aptitude using apt')
        print( '    apt:')
        print( '      name: aptitude')
        print( '      state: latest')
        print( '      update_cache: yes')
        print( '      force_apt_get: yes')
        print( '  - name: Install dependencies for Docker')
        print( '    apt:')
        print( '      name:')
        print( '      - apt-transport-https')
        print( '      - ca-certificates')
        print( '      - gnupg-agent')
        print( '      - software-properties-common')
        print( '      - python3-pip')
        print( '      update_cache: yes')
        print( '      state: present')
        print( '  - name: Add official GPG key of Docker')
        print( '    apt_key:')
        print( '      url: https://download.docker.com/linux/ubuntu/gpg')
        print( '      state: present')
        print( '  - name: Add Docker repository')
        print( '    apt_repository:')
        print( '      repo: deb https://download.docker.com/linux/ubuntu bionic stable')
        print( '      state: present')
        print( '  - name: Install Docker')
        print( '    apt:')
        print( '      name:')
        print( '      - docker-ce')
        print( '      - docker-ce-cli')
        print( '      - containerd.io')
        print( '      update_cache: yes')
        print( '      state: present')
        print( '  - name: Add user to docker group')
        print( '    user:')
        print(f'      name: {username}')
        print( '      groups: docker')
        print( '      append: yes')
        print( '  - name: Install Docker Compose')
        print( '    get_url:')
        print( '      url: https://github.com/docker/compose/releases/download/1.25.5/docker-compose-Linux-x86_64')
        print( '      dest: /usr/local/bin/docker-compose')
        print( '      mode: "0755"')
        print( '  - name: Create symbolic link for Docker Compose')
        print( '    file:')
        print( '      src: /usr/local/bin/docker-compose')
        print( '      dest: /usr/bin/docker-compose')
        print( '      state: link')
        print( '  - name: Upgrade PIP')
        print( '    shell: python3 -m pip install -U pip')
        print( '  - name: Install Python modules')
        print( '    pip:')
        print( '      name:')
        print( '      - docker')
        print( '      - docker-compose')
        print( '      state: latest')
        print( '  - name: Pull ZooKeeper Docker image')
        print( '    docker_image:')
        print( '      name: nexgus/zookeeper:3.6.1')
        print( '      source: pull')
        print( '  - name: Pull Kafka Docker image')
        print( '    docker_image:')
        print( '      name: nexgus/kafka:2.12-2.4.1')
        print( '      source: pull')

        if args.mount:
            device, mount_point = mount.split(':')
            print( '  - name: Install partition tool')
            print( '    apt:')
            print( '      name: parted')
            print( '      state: present')
            print( '  - name: Create partition for data disk')
            print( '    parted:')
            print(f'      device: {device}')
            print( '      number: "1"')
            print( '      state: present')
            print( '  - name: Format data disk')
            print( '    filesystem:')
            print(f'      device: {device}1')
            print( '      force: yes')
            print( '      fstype: ext4')
            print( '  - name: Create a mount point for data disk')
            print( '    file:')
            print(f'      path: {mount_point}')
            print( '      state: directory')
            print( '  - name: Mount data disk')
            print( '    mount:')
            print(f'      path: {mount_point}')
            print(f'      src: {device}1')
            print( '      fstype: ext4')
            print( '      state: mounted')
            print( '  - name: Create data directory for ZooKeeper')
            print( '    file:')
            print(f'      path: {mount_point}/zookeeper')
            print( '      state: directory')
            print( '  - name: Create data directory for Kafka')
            print( '    file:')
            print(f'      path: {mount_point}/kafka')
            print( '      state: directory')

        # For each server
        for idx, host in enumerate(host_ip):
            print()
            print(f'- hosts: server{idx+1}')
            print( '  become: true')
            print( '  tasks:')
            print( '  - name: Run ZooKeeper and Kafka')
            print( '    docker_compose:')
            print( '      project_name: nexcom')
            print( '      definition:')
            print( '        version: "2"')
            # Named volumes
            if (not zookeeper_volume.startswith('/')) or (not kafka_volume.startswith('/')):
                print( '        volumes:')
                if not zookeeper_volume.startswith('/'):
                    print(f'          {zookeeper_volume}:')
                    print( '            driver: local')
                if not kafka_volume.startswith('/'):
                    print(f'          {kafka_volume}:')
                    print( '            driver: local')
            # Services
            print( '        services:')
            print( '          zookeeper:')
            print( '            image: nexgus/zookeeper:3.6.1')
            print( '            ports:')
            print( '            - 2181:2181')
            print( '            - 2888:2888')
            print( '            - 3888:3888')
            print( '            volumes:')
            print(f'            - {zookeeper_volume}:/var/lib/zookeeper')
            print( '            environment:')
            print(f'              ZK_ID: "{idx+1}"')
            print( '              ZK_dataDir: /var/lib/zookeeper')
            for server, ip in enumerate(private_ip):
                print(f'              ZK_server_{server+1}: {ip}:2888:3888')
            print( '            restart: unless-stopped')
            print( '          kafka:')
            print( '            image: nexgus/kafka:2.12-2.4.1')
            print( '            ports:')
            print( '            - 9092:9092')
            print( '            - 9094:9094')
            print( '            volumes:')
            print(f'            - {kafka_volume}:/var/lib/kafka')
            print( '            environment:')
            print(f'              KK_BROKER_ID: "{idx}"')
            print( '              KK_LOG_DIR: /var/lib/kafka')
            print(f'              KK_LOG_RETENTION_HOURS: {kafka_retention_hours}')
            print(f'              KK_LOG_RETENTION_BYTES: {kafka_retention_bytes}')
            print( '              KK_LISTENERS: INTRANET://0.0.0.0:9094,INTERNET://0.0.0.0:9092')
            print(f'              KK_ADVERTISED_LISTENERS: INTRANET://{private_ip[idx]}:9094,INTERNET://{public_ip[idx]}:9092')
            print( '              KK_LISTENER_SECURITY_PROTOCOL_MAP: INTRANET:PLAINTEXT,INTERNET:PLAINTEXT')
            print( '              KK_INTER_BROKER_LISTENER_NAME: INTRANET')
            print( '              KK_ZOOKEEPER_CONNECT: ', end='')
            print( ','.join([f'{ip}:2181/{args.kafka_chroot}' for ip in private_ip]))
            print( '            restart: unless-stopped')

    sys.stdout = stdout

###############################################################################
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
        username=args.user,
        kafka_volume=args.kafka_volume,
        zookeeper_volume=args.zookeeper_volume,
        mount=args.mount,
    )

###############################################################################
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
    parser.add_argument('-krh', '--kafka-retention-hours', 
                        type=int,
                        default=168, 
                        help='The number of hours to keep a log file before '
                             'deleting it (in hours) for Kafka cluster.')
    parser.add_argument('-krb', '--kafka-retention-bytes', 
                        type=int,
                        default=-1, 
                        help='The maximum size (in bytes) of the log before '
                             'deleting it for Kafka cluster.')
    parser.add_argument('-kch', '--kafka-chroot', 
                        type=str,
                        default='kafka',
                        help='A Kafka server can also have a ZooKeeper chroot '
                             'path as part of its ZooKeeper connection string '
                             'which puts its data under some path in the '
                             'ZooKeeper names.')
    parser.add_argument('-m', '--mount',
                        type=str,
                        help='Data disk mount info in format "<device>:<mount '
                             'point>". If --mount is set, --zookeeper-volume '
                             'and --kafka-volume will be set automatically.')
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

    if args.kafka_chroot.startswith('/')::
        args.kafka_chroot = args.kafka_chroot[1:]

    main(args)
