# Chocolatey for Business Ansible Environment

## Deployment

To deploy the Chocolatey for Business Ansible Environment, first, clone the repository to your chosen Ansible environment, make the following modifications, and deploy the `c4b-environment.yml` playbook.

Create hosts. Depending on your chosen configuration, you may not need to create all of them:

| Group           | Purpose                                                                      |
| --------------- | ---------------------------------------------------------------------------- |
| ccm_server      | Runs the Chocolatey Central Management service and administration interface. |
| nexus_server    | Runs Sonatype Nexus Repository, to store and distribute packages.            |
| jenkins_server  | Runs Jenkins, to run jobs to updating packages in the Nexus repository.      |
| database_server | Runs SQL Server Express, to store information from the CCM service.          |

By default, any non-specified service will be installed on the ccm_server host.

You should provide the following arguments:

| Argument                   | Purpose                                            |
| -------------------------- | -------------------------------------------------- |
| license_path               | Your Chocolatey for Business license file.         |
| certificate_path           | The PFX certificate to use for all HTTPS services. |
| certificate_password       | The password for the PFX certificate.              |

Depending on the way Ansible has been installed it might be required to install the collections used in this playbook.
Use the following command to install the collections locally to this playbook:

```bash
ansible-galaxy collection install -r collections/requirements.yml -p collections
```

Finally, you can deploy the playbook as follows (using the example hosts file):

`ansible-playbook ./c4b-environment.yml -i ./hosts.yml`

You will be prompted for any values you have not provided in `--extra-vars` or another fashion. An example of passing a variable on the command-line is as follows:

`ansible-playbook ./c4b-environment --extra-vars "license_path=/path/to/chocolatey.license.xml certificate_path=/path/to/certificate.pfx"`

You can also define variables in AWX, or within a file. For further details, see [Defining variables at runtime](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#passing-variables-on-the-command-line).

For further information on deploying this environment, see [the docs page](https://docs.chocolatey.org/en-us/c4b-environments/ansible/).

## Hardware Recommendations

We recommend the following configuration if deploying to a single Ansible host:

-  Windows Server 2019+
-  4+ CPU cores
-  16 GB+ RAM (8GB as a bare minimum; 4GB of RAM is reserved specifically for Nexus)
-  500 GB+ of free space for local NuGet package artifact storage

If deploying to multiple hosts, please refer to the recommended specifications for:

- [Chocolatey Central Management](https://docs.chocolatey.org/en-us/central-management/setup/#high-level-requirements)
- [Sonatype Nexus Repository](https://help.sonatype.com/repomanager3/product-information/sonatype-nexus-repository-system-requirements)
- [Jenkins](https://www.jenkins.io/doc/book/installing/windows/#prerequisites)
- [SQL Server Express](https://www.microsoft.com/en-us/download/details.aspx?id=104781)

## Offline Installation

To install in an air-gapped environment, you can download this repository to a local machine and run the `OfflineInstallPreparation.ps1` script.

This script downloads all the required files and packages to ensure a successful installation. Please note that you will require a Windows machine with a licensed copy of Chocolatey, as it utilises the Package Internalizer feature.

After the script has run, copy the directory to your Ansible environment and deploy it.

## Storing Secrets

After the playbook has run, various secrets will have been created and stored in the `/credentials` directory. To keep these secure, you should use [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html) or something similar to store and inject them instead of the password lookup files, as `lookup('ansible.builtin.password'` does not support encryption or Ansible Vault. To do so, follow these steps for each secret (using `ccm_client_salt` as the example):

- In a terminal on your Ansible machine, run `ansible-vault encrypt /path/to/repository/credentials/ccm_client_salt`.
- Open the `/path/to/repository/credentials/ccm_client_salt` file and copy the new contents of the file.
- Open the `./group_vars/all.yml` file and overwrite the value of `ccm_client_salt` with the vaulted value.

This will result in re-deployment of the environment using this secret, going forward.

If you want to re-deploy the environment having changed your passwords, or initially deploy it using your own generated values, you can use `ansible-vault` and the `all.yml` file to deploy using those values.

- In a terminal on your Ansible machine, run `ansible-vault encrypt_string 'some-secure-password-here' --name 'ccm_client_salt'`.
- Open the `./group_vars/all.yml` file and overwrite the line beginning `ccm_client_salt:` with the output of the `ansible-vault` command.