KPI Dashboard - Export EDI
Outil de génération automatique de tableaux de bord KPI pour le suivi des exports EDI.

🎯 Pour le Client
Installation Simple
Téléchargez KPI_Dashboard.exe depuis les Releases
Téléchargez config.txt et modifiez avec vos paramètres de base de données
Placez les deux fichiers dans le même dossier
Double-cliquez sur KPI_Dashboard.exe
Configuration de la Base de Données
Modifiez le fichier config.txt :

HOST=votre_serveur_postgres
DATABASE=votre_base_de_donnees
USER=votre_utilisateur
PASSWORD=votre_mot_de_passe
PORT=5432
Utilisation Quotidienne
Double-cliquez sur KPI_Dashboard.exe
Le tableau de bord s'ouvre automatiquement dans votre navigateur
Un nouveau fichier HTML est créé chaque jour
🔄 Mise à Jour Automatique
Ce repository utilise GitHub Actions pour créer automatiquement l'exécutable Windows à chaque modification du code.

📊 KPIs Inclus
Pièces exportées par dossier
Écritures exportées par dossier
Pièces en attente de traitement
Écritures en attente de traitement
Comptes d'attente (47%)
Dates min/max des pièces à traiter
