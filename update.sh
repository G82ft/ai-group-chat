cd ai-group-chat || exit
git pull && docker build . -t agc && docker rm -f agc
docker run -v "$HOME"/agc/data:/app/data -v "$HOME"/agc/config:/app/config --name agc -itd agc