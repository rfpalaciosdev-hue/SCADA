# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./
RUN npm install

# Copiar el resto del código
COPY . .

# Construir para producción
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine

# Copiar los archivos construidos desde el stage anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Copiar configuración personalizada de Nginx si es necesario (para SPA)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
