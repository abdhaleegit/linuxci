import groovy.json.JsonSlurper
def base_dir="/var/lib/jenkins/workspace/gitbisect"
def test_result = 1
def state = 'Failed at start'
node ('built-in') {
    properties([parameters([string(defaultValue: 'default-lpar', description: '', name: 'lpar_name', trim: false), string(defaultValue: 'default-linux-repo', description: '', name: 'linux_repo', trim: false), string(defaultValue: 'build_bisect', description: '', name: 'linux_branch', trim: false), string(defaultValue: 'default-config', description: '', name: 'linux_config', trim: false),  string(defaultValue: 'default-sid', description: '', name: 'sid', trim: false), string(defaultValue: "1" , description: '', name: 'bisect_flag',trim: false), ]),])
    try {
         stage('Clone op-test') {
            state = "Failed during op-test clone"
            def exists = fileExists('op-test')
                if (!exists){
                    new File('op-test').mkdir()
                }
            dir ('op-test') {
            git branch: 'new_bisect_build', url: 'op-test-github-link'
            }
        
        }
        stage('Clone linuxci') {
            state = "Failed during linuxci clone"
            def exists = fileExists 'linuxci'
                if (!exists){
                    new File('linuxci').mkdir()
                }
            dir ('linuxci') {
            git branch: 'process', url: 'linuxci.git'
            }
            
        }
        stage('Fetch good commit') {
            state = "Failed during fetching good commit"
            def linad = "/linuxci/jenkins-ci/process.py"
            def finad = base_dir+linad
            echo "add is ${finad}"
            def ab = fileExists('${finad}')
            echo " ans is ${ab}"
            def goodcommit= sh(returnStdout: true, script: 'python3 /var/lib/jenkins/workspace/gitbisect/linuxci/jenkins-ci/process.py "KORG#71" "build" ')
            echo " good commit is ${goodcommit}"
            env.GOOD_COMMIT = goodcommit
            
        }
        stage('Op-test config') {
            state = "Failed to test Git Bisect"
            dir('op-test'){
                sh '''#!/bin/bash
                wget machine-conf-for-optest -O machine.conf
                '''
            }
            
        }
        stage('Doing Build Git Bisect Test') {
            state = "Failed to test Git Bisect"
            goodcommit = env.GOOD_COMMIT
            echo "good is ${goodcommit}"
            dir('op-test'){
                    sh """#!/bin/bash
                    
                    echo "repo:   ${linux_repo}"
                    echo "good commi:   ${goodcommit}"
                    
                python op-test --run testcases.OpTestKernelTest.KernelBuild -c machine.conf --bisect-flag=${bisect_flag} --lpar-name=${lpar_name} \\
                --git-repo=${linux_repo} --git-branch=${linux_branch} --git-repoconfigpath=${linux_config} --good-commit=${goodcommit}"""
            }

        } 
        }
        catch (e) {	
        throw e
    }
    finally {
        stage('Commit Updation'){
            def path = "/var/lib/jenkins/workspace/gitbisect/op-test/output.json"
            def JSONpath = path
            echo "JSONPATH IS ${JSONpath}"
            if(fileExists('output.json')){
                    echo "File exits "
                }
            def data = readJSON file : JSONpath
            echo " ${data} "
            echo " ${data} "
            def exit_code = data.exit_code
            def email = data.email
            def commit = data.commit
            def error = data.error
            echo "ENTERED COMMIT UPDATION"
            if(exit_code != 0){
                echo "${commit}  ${email} ${error} is the cred."
            }
            else{
                def val = !linux_repo.endsWith("linux-next.git")
                echo "${val}"
                if(!linux_repo.endsWith("linux-next.git")){
                    sh """
                python3 /var/lib/jenkins/workspace/gitbisect/linuxci/jenkins-ci/process.py 'KORG#71' '${commit}' 'build' 
                """
                }
            JSONdata = null
            }
        }
        stage('Sending email'){
            if(bisect_flag != '1' ){
                echo "${bisect_flag}"
                echo "no email "
            }
            else{
                def email_path = "/var/lib/jenkins/workspace/gitbisect/op-test/email.json"
                def email_JSONpath = email_path
                if(fileExists(email_JSONpath)){
                        echo "File exits "
                    }
                    
                def email_data = readJSON file : email_JSONpath
                echo " ${email_data} "
                // def em_JSONdata = new JsonSlurper().parseText(email_data)
                def subject = email_data.subject
                def body = email_data.body
                echo "subject"
                echo "${subject}"
                echo "${body}"
                mail bcc: '', body: body, cc: '', from: '', replyTo: '', subject:"${subject}", to: ''
                
            }
            
        }
    }

    
}
