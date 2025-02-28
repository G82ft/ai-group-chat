cd ai-group-chat || exit
git pull && docker build . -t agc && docker rm -f agc
docker run --mount type=bind,src=~/agc/data,dst=/app/data,bind-propagation=shared -v ~/agc/config:/app/config --name agc agc