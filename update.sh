cd ai-group-chat || exit
git pull && docker buildx build . -t agc && docker rm -f agc
docker run --mount type=bind,src="$HOME"/agc/data,dst=/app/data --name agc -itd --rm agc