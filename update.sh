cd ai-group-chat || exit
git pull && docker buildx build . -t agc && docker rm -f agc
docker run -v "$HOST"/agc/data:/app/data -v "$HOST"/agc/config:/app/config --name agc -itd agc