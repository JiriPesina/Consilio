# 0. Výchozí image
FROM node:20

# 1. Pracovní adresář
WORKDIR /app

# 2. Zkopírujeme jen package.json a package-lock.json
COPY ./consilio_vue/package*.json ./

# 3. Nainstalujeme všechny závislosti (včetně vuedraggable, protože je v package.json)
RUN npm install

# 4. Zkopírujeme zbytek zdrojáků
COPY ./consilio_vue ./

# 5. Spustíme vývojový server
CMD ["npm", "run", "serve"]