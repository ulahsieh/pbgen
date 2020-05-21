# Deploy A Kafka Cluster to Azure
1.  Generate a key pair in `~/.ssh`. If there is not `~/.ssh` in your machine, use this command to create.  
    ```bash
    mkdir -p ~/.ssh
    ```
    The following command will create an RSA priviate key `kafka_rsa`, and a public key `kafka_rsa.pub`.
    ```bash
    $ ssh-keygen -t rsa -f ~/.ssh/kafka_rsa -N "" -q
    ```
1.  We will generate three VMs in Azure resource group `kafka`.
    ```bash
    python3 azvm.py create kafka -v kafka -q 3 -d gus-kafka -u deployer -k ~/.ssh/kafka_rsa.pub
    ```
1.  Check the info of VMs.
    ```bash
    python3 azvm.py info kafka
    ```  
    The message looks like
    ```
    ==============================
    Name: kafka1 (running)
        Private IP: 10.0.0.4
        Public IP: 52.250.22.6 (Dynamic)
        FQDN: gus-kafka1.westus2.cloudapp.azure.com
    ==============================
    Name: kafka2 (running)
        Private IP: 10.0.0.5
        Public IP: 52.250.64.219 (Dynamic)
        FQDN: gus-kafka2.westus2.cloudapp.azure.com
    ==============================
    Name: kafka3 (running)
        Private IP: 10.0.0.6
        Public IP: 51.143.38.160 (Dynamic)
        FQDN: gus-kafka3.westus2.cloudapp.azure.com
    ```
1.  Generate a playbook to install Kafka cluster on those VMs.
    ```bash
    python3 playbookgen.py \
        --private-ip 10.0.0.4 \
                     10.0.0.5 \
                     10.0.0.6 \
        --public-ip gus-kafka1.westus2.cloudapp.azure.com \
                    gus-kafka2.westus2.cloudapp.azure.com \
                    gus-kafka3.westus2.cloudapp.azure.com \
        --user deployer \
        --key ~/.ssh/kafka_rsa
    ```
1.  Let's deploy Kafka cluster to VMs.
    ```bash
    cd playbook
    ansible-playbook deploy.yml
    ```
1.  If you want to ssh to a VM, using one of the following commands depends on the host address of VM.
    ```bash
    ssh deployer@gus-kafka1.westus2.cloudapp.azure.com -i ~/.ssh/kafka_rsa
    ssh deployer@gus-kafka2.westus2.cloudapp.azure.com -i ~/.ssh/kafka_rsa
    ssh deployer@gus-kafka3.westus2.cloudapp.azure.com -i ~/.ssh/kafka_rsa
    ```