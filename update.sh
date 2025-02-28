cd ai-group-chat || exit
git pull && docker buildx build . -t agc && docker rm -f agc
docker run -v agc/data:/app/data -v agc/config:/app/config --name agc -itd --rm agc