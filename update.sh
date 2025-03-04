cd ai-group-chat || exit
git pull && docker buildx build . -t agc && docker rm -f agc
docker run -v /var/lib/agc/chats:/app/chats -v /var/lib/agc/config:/app/config --name agc -itd agc