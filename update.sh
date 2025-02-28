cd ai-group-chat || exit
git pull && docker build . -t agc && docker rm -f agc
docker run --name agc -itd --rm agc