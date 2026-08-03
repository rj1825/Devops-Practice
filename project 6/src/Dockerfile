FROM nginx:alpine

# Copy the custom dashboard HTML file to the default Nginx web root directory
COPY index.html /usr/share/nginx/html/index.html

# Expose port 80 for web traffic
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
