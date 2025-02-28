cd ai-group-chat || exit
git pull && docker build . -t agc && docker rm -f agc
docker run --mount type=bind,src="$HOME"/agc/data,dst=/app/data,bind-propagation=shared -v /root/agc/config:/app/config --name agc agc