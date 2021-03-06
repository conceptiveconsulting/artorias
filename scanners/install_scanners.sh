#!/bin/bash

function startup_checks () {
    if [[ $EUID -ne 0 ]];
    then 
        echo "[X] Install scanners needs to run as root.."
        exit 1
    fi
}

function does_source_exist () {
    # If directory does not exist, return 1
    scanner=$1

    # Check if scanner source installed
    if [[ ! -d "$scanner" ]];
    then
        echo 1
    else
        echo 0
    fi
}

function does_cmd_exist () {
    # If command does not exist return 1
    cmd=$1
    which "$cmd" > /dev/null

    # Check if cmd found in PATH
    if [[ $? -eq 0 ]];
    then
        return 0
    else
        return 1
    fi
}

function install_source () {
    name=$1
    repo=$2

    git clone "$repo"
    pushd "$name"

    if [[ -f requirements.txt ]];
    then
        pip3 install -r requirements.txt
        if [[ $? -ne 0 ]];
        then
            echo "[!!] Errors may have occurred installing required packages.."
            echo "for: $name"
        else
            echo "[**] Packages successfully installed for $name"
        fi
    fi

    popd
}

function install_cmd () {

    program=$1

    # TODO make more portable by adjusting package manager as well
    apt-get -y install "$program"

    if [[ $? -ne 0 ]];
    then
        echo "[!!] Errors may hav occurred installing scanner.."
        echo "for: $program"
    else
        echo "[**] Command successfully installed for $program"
    fi

}

function install_scanner () {

    scanner=$1
    stype=$2
    repo=$3

    if [[ $stype = "source" ]];
    then
        chk=$(does_source_exist "$scanner")
        if [[ $chk -ne 0 ]];
        then
            echo "[**] Setting up the $scanner!"
            install_source "$scanner" "$repo"
        else
            echo "[**] $scanner already installed, skipping install..."
        fi
    else
        chk=$(does_cmd_exist "$scanner")
        if [[ $chk -eq 0 ]];
        then
            echo "[**] Setting up $scanner!"
            install_cmd "$scanner"
        else
            echo "[**] $scanner already installed, skipping install.."
        fi
    fi
}

function install_zap () {
    # I didnt want to have to make custom stuff, but there's really no great way of
    # automating this scanners installation..
    wget -nd "https://github.com/zaproxy/zaproxy/wiki/Downloads/ZAP_2.7.0_Linux.tar.gz"
    tar -xf "ZAP_2.7.0_Linux.tar.gz"
    pushd "ZAP_2.7.0"

    ln -s "zap.sh" "/usr/bin/zaproxy"

    popd

    if [[ $(which zaproxy) -ne 0 ]];
    then
        echo "[!!] Errors may have occurred installing OWASP-Zap.."
    else
        echo "[**] Command successfully installed for OWASP-Zap"
    fi
}

function get_wordlist () {
    if [[ ! -f rockyou.txt ]];
    then
        echo "[**] Installing rockyou wordlist"
        url="downloads.skullsecurity.org/passwords/rockyou.txt.bz2"
        wget -nd $url
        bzip2 -d rockyou.txt.bz2

    else
        echo "[**] rockyou wordlist already installed"
    fi
}

echo "[**] Installing some scanners for Artorias!!"
echo "[**] Doing some startup checks.."

startup_checks

pushd "sources"

# Install the scanners from souce at Github
install_scanner "OWASP-Nettacker" "source" \
    "https://github.com/zdresearch/OWASP-Nettacker.git"

install_scanner "testssl.sh" "source" \
    "https://github.com/drwetter/testssl.sh.git"

# Needed custom code for getting latest hydra version for output formats
chk=$(does_source_exist "hydra")
if [[ $chk -ne 0 ]];
then
    apt-get install -y "libssl-dev libssh-dev libidn11-dev libpcre3-dev" \
                    "libgtk2.0-dev libmysqlclient-dev libpq-dev libsvn-dev" \
                    "firebird-dev"

    git clone 'https://github.com/vanhauser-thc/thc-hydra.git'
    pushd thc-hydra
    ./configure && make && make install

    if [[ $? -ne 0 ]];
    then 
        echo "[!!] Errors may have occurred configuring scanner from source.."
        echo "for: hydra"
    else
        echo "[**] Packages successfully installed for hydra"
    fi
    popd
fi

# Install these scanners through the package manager
install_scanner "nikto" "cmd"
nikto -update

install_scanner "nmap" "cmd"
install_scanner "skipfish" "cmd"
install_zap

get_wordlist

echo "[**] All compatable scanners have been added!"
popd

exit 0
