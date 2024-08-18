#!/usr/bin/env bash

TOOLING_SH="/usr/local/bin/tooling.sh"
_REMOTE_MINIKUBE_CONFIG="/usr/local/share/minikube-remote"
_REMOTE_KUBE_CONFIG="/usr/local/share/kube-remote"
_REMOTE_IP=$(nslookup -type=a host.docker.internal  | grep Address | tail -n 1 | cut -d ' ' -f 2)

apk --no-cache add \
    kubectl \
    kubectl-bash-completion \
    helm \
    docker-cli \
    docker-cli-buildx \
    docker-cli-compose \
    docker-bash-completion \
    socat

if false ; then
    apk --no-cache add make go

    # We need to build this from the sources.
    TELEPRESENCE_VERSION='v2.19.1'
    git clone https://github.com/telepresenceio/telepresence.git -b $TELEPRESENCE_VERSION /tmp/telepresence
    make -C /tmp/telepresence TELEPRESENCE_VERSION=$TELEPRESENCE_VERSION bindir=/usr/local/bin install
    rm -rf /tmp/telepresence
    apk --no-cache del make go
fi

cat >"$TOOLING_SH" <<EOF
#!/usr/bin/env bash
if test -d "${_REMOTE_KUBE_CONFIG}"; then
    mkdir -p ${_REMOTE_USER_HOME}/.kube
    sudo cp -r ${_REMOTE_KUBE_CONFIG}/* ${_REMOTE_USER_HOME}/.kube
    sudo chown -R ${_REMOTE_USER}: ${_REMOTE_USER_HOME}/.kube
    chmod 600 ${_REMOTE_USER_HOME}/.kube/config
fi

if test -d "${_REMOTE_MINIKUBE_CONFIG}"; then
    mkdir -p ${_REMOTE_USER_HOME}/.minikube
    sudo cp -r ${_REMOTE_MINIKUBE_CONFIG}/ca.crt ${_REMOTE_USER_HOME}/.minikube
    if [ -f "${_REMOTE_MINIKUBE_CONFIG}/client.crt" ]; then
        sudo cp -r ${_REMOTE_MINIKUBE_CONFIG}/client.crt ${_REMOTE_USER_HOME}/.minikube
        sudo cp -r ${_REMOTE_MINIKUBE_CONFIG}/client.key ${_REMOTE_USER_HOME}/.minikube
    elif [ -f "${_REMOTE_MINIKUBE_CONFIG}/profiles/minikube/client.crt" ]; then
        sudo cp -r ${_REMOTE_MINIKUBE_CONFIG}/profiles/minikube/client.crt ${_REMOTE_USER_HOME}/.minikube
        sudo cp -r ${_REMOTE_MINIKUBE_CONFIG}/profiles/minikube/client.key ${_REMOTE_USER_HOME}/.minikube
    fi
    sudo chown -R ${_REMOTE_USER}: ${_REMOTE_USER_HOME}/.minikube
    chmod 600 ${_REMOTE_USER_HOME}/.minikube/*

    sed -i -r "s|(\s*certificate-authority:\s).*|\\1${_REMOTE_USER_HOME}\/.minikube\/ca.crt|g" ${_REMOTE_USER_HOME}/.kube/config
    sed -i -r "s|(\s*client-certificate:\s).*|\\1${_REMOTE_USER_HOME}\/.minikube\/client.crt|g" ${_REMOTE_USER_HOME}/.kube/config
    sed -i -r "s|(\s*client-key:\s).*|\\1${_REMOTE_USER_HOME}\/.minikube\/client.key|g" ${_REMOTE_USER_HOME}/.kube/config
    sed -i -e "s/localhost/minikube/g" ${_REMOTE_USER_HOME}/.kube/config
    sed -i -e "s/127.0.0.1/minikube/g" ${_REMOTE_USER_HOME}/.kube/config
    sudo sh -c 'echo "${_REMOTE_IP} minikube" >> /etc/hosts'
else
    sed -i -e "s/localhost/host.docker.internal/g" ${_REMOTE_USER_HOME}/.kube/config
    sed -i -e "s/127.0.0.1/host.docker.internal/g" ${_REMOTE_USER_HOME}/.kube/config
fi
sudo nohup setsid socat UNIX-LISTEN:/var/run/docker.sock,fork,mode=660,user=${_REMOTE_USER} UNIX-CONNECT:/var/run/docker-host.sock 2>/dev/null >/dev/null
EOF

chmod +x "$TOOLING_SH"
