pwd
git pull && docker build . -t agc && docker rm -f agc && docker run -v ~/agc/data:/app/data -v ~/agc/config:/app/config --name agc