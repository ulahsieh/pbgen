#/usr/bin/env python3
# -*- coding: utf-8 -*-
import ansible_utils as utils
import errno
import os
import yaml

from collections import OrderedDict

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
             username='deployer',
             kafka_volume='kafka', 
             zookeeper_volume='zookeeper', 
             mount=None):

    yml_all = OrderedDict()
    yml_all['hosts'] = 'all'
    yml_all['become'] = True
    yml_all['tasks'] = []
    yml_all['tasks'].append(utils.apt(
        desc='Install aptitude using apt',
        name='aptitude',
        state='present',
        update_cache='yes',
        force_apt_get: 'yes',
    ))
    yml_all['tasks'].append(utils.apt(
        desc='Install dependencies for Docker',
        name=[
            'apt-transport-https', 
            'ca-certificates', 
            'gnupg-agent', 
            'software-properties-common', 
            'python3-pip',
        ],
        state='present',
    ))
    yml_all['tasks'].append(utils.apt_key(
        desc='Add official GPG key for Docker',
        url='https://download.docker.com/linux/ubuntu/gpg',
        state='present',
    ))
    yml_all['tasks'].append(utils.apt_repository(
        desc='Add Docker repository',
        url='deb https://download.docker.com/linux/ubuntu bionic stable',
        state='present',
    ))
    yml_all['tasks'].append(utils.apt(
        desc='Install Docker',
        name=[
            'docker-ce',
            'docker-ce-cli',
            'containerd.io',
        ],
        state='present',
        update_cache='yes',
    ))
    yml_all['tasks'].append(utils.user(
        desc='Add user to docker group',
        name=f'{username}',
        groups='docker',
        append='yes',
    ))
    yml_all['tasks'].append(utils.get_url(
        desc='Install Docker Compose',
        url='https://github.com/docker/compose/releases/download/1.25.5/docker-compose-Linux-x86_64',
        dest='/usr/local/bin/docker-compose',
        mode='0755',
    ))
    yml_all['tasks'].append(utils.file(
        desc='Create symbolic link for Docker Compose',
        src='/usr/local/bin/docker-compose',
        dest='/usr/bin/docker-compose',
        state='link',
    ))
    yml_all['tasks'].append(utils.shell(
        desc='Upgrade pip',
        shell='python3 -m pip install -U pip',
    ))
    yml_all['tasks'].append(utils.pip(
        desc='Install Python modules',
        name=[
            'docker',
            'docker-compose',
        ],
        state='latest',
    ))
    yml_all['tasks'].append(utils.docker_image(
        desc='Pull ZooKeeper Docker image',
        name='nexgus/zookeeper:3.6.1'
        source='pull',
    ))
    yml_all['tasks'].append(utils.docker_image(
        desc='Pull Kafka Docker image',
        name='nexgus/kafka:2.12-2.4.1',
        source='pull',
    ))

    # If there is external data disk
    if mount:
        device, mount_point = mount.split(':')
        yml_all['tasks'].append(utils.apt(
            desc='Install partition tool',
            name='parted',
            state='present',
        ))
        yml_all['tasks'].append(utils.parted(
            desc='Create partition for data disk',
            device=f'{device}',
            number='1',
            state='present',
        ))
        yml_all['tasks'].append(utils.filesystem(
            desc='Format data disk',
            device=f'{device}1',
            force='yes',
            fstype='ext4',
        ))
        yml_all['tasks'].append(utils.file(
            desc='Create a mount point for data disk',
            path=f'{mount_point}',
            state='directory',
        ))
        yml_all['tasks'].append(utils.mount(
            desc='Mount data disk',
            path=f'{mount_point}',
            src=f'{device}1',
            fstype='ext4',
            state='mounted',
        ))
        yml_all['tasks'].append(utils.file(
            desc='Create data directory for ZooKeeper',
            path=f'{mount_point}/zookeeper',
            state='directory',
        ))
        yml_all['tasks'].append(utils.file(
            desc='Create data directory for Kafka',
            path=f'{mount_point}/kafka',
            state='directory',
        ))

    yml = [yml_all]
    for idx, host in enumerate(host_ip):
        # ZooKeeper Docker Compose file content
        env = utils.ordered_dict(
            'ZK_ID', 'ZK_dataDir',
            ZK_ID=f'{idx+1}',
            ZK_dataDir='/var/lib/zookeeper',
        )
        for server, ip in enumerate(private_ip):
            env[f'ZK_server_{server+1}'] = f'{ip}:2888:3888'
        zookeeper = utils.ordered_dict(
            'image', 'ports', 'volumes', 'environment', 'restart',
            image='nexgus/zookeeper:3.6.1',
            ports=['2181:2181', '2888:2888', '3888:3888'], 
            volumes=[f'{zookeeper_volume}:/var/lib/zookeeper'], 
            environment=env, 
            restart='unless-stopped', 
        )

        # Kafka Docker Compose file content
        env = ordered_dict(
            'KK_BROKER_ID', 'KK_LOG_DIR', 'KK_LISTENERS', 
            'KK_ADVERTISED_LISTENERS', 'KK_LISTENER_SECURITY_PROTOCOL_MAP',
            'KK_INTER_BROKER_LISTENER_NAME', 'KK_ZOOKEEPER_CONNECT', 
            'KK_LOG_ROLL_HOURS', 'KK_ZOOKEEPER_CONNECTION_TIMEOUT_MS',
            KK_BROKER_ID=f'{idx}',
            KK_LOG_DIR='/var/lib/kafka',
            KK_LISTENERS='INTRANET://0.0.0.0:9094,INTERNET://0.0.0.0:9092',
            KK_ADVERTISED_LISTENERS=f'INTRANET://{private_ip[idx]}:9094,'
                                    f'INTERNET://{public_ip[idx]}:9092',
            KK_LISTENER_SECURITY_PROTOCOL_MAP='INTRANET:PLAINTEXT,'
                                              'INTERNET:PLAINTEXT',
            KK_INTER_BROKER_LISTENER_NAME='INTRANET',
            KK_ZOOKEEPER_CONNECT=','.join([
                f'{ip}:2181' for ip in private_ip]),
            KK_LOG_ROLL_HOURS='168', # 7 days
            KK_ZOOKEEPER_CONNECTION_TIMEOUT_MS=60*60*1000, # an hour
        )
        kafka = ordered_dict(
            'image', 'ports', 'volumes', 'environment', 'restart',
            image='nexgus/kafka:2.12-2.4.1', 
            ports=['9092:9092', '9094:9094'], 
            environment=env, 
            restart='unless-stopped', 
        )

        docker_compose = ordered_dict(
            'name', 'docker_compose', 
            name='Run ZooKeeper and Kafka', 
            docker_compose=ordered_dict(
                'project_name', 'definition',
                project_name='nexcom',
                definition=ordered_dict(
                    'version', 'services', 
                    version='2',
                    services=ordered_dict(
                        'zookeeper', 'kafka',
                        zookeeper=zookeeper,
                        kafka=kafka,
                    ),
                ),
            ),
        )
--------------------
        # Named volume definition(s)
        if not zookeeper_volume.startswith('/'):
            yml_server['tasks'][0]['docker_compose']['definition']['volumes'] = {
                f'{zookeeper_volume}': {
                    'driver': 'local'
                }
        }
        if not kafka_volume.startswith('/'):
            yml_server['tasks'][0]['docker_compose']['definition']['volumes'] = {
                f'{kafka_volume}': {
                    'driver': 'local'
                }
        }

        yml.append(yml_server)

    with open(filepath, 'w') as fp:
        fp.write(yaml.dump(yml))

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
        username=args.user,
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
                        default='./playbook',
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
