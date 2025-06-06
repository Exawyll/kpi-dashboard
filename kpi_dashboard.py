#!/usr/bin/env python3
"""
KPI Dashboard Generator for EDI Export Tracking
Simple tool to generate daily KPI reports from PostgreSQL database
"""

import psycopg2
import pandas as pd
from datetime import datetime, date
import os
from pathlib import Path

# Database configuration - Load from config file or environment
def load_config():
    """Load database configuration from config.txt file or environment variables"""
    config = {}
    
    # Try to load from config.txt file first
    if os.path.exists('config.txt'):
        with open('config.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip().lower()] = value.strip()
    
    # Fallback to default values if not found
    return {
        'host': config.get('host', 'localhost'),
        'database': config.get('database', 'your_database'),
        'user': config.get('user', 'your_username'), 
        'password': config.get('password', 'your_password'),
        'port': int(config.get('port', 5432))
    }

DB_CONFIG = load_config()

# SQL Queries
QUERIES = {
    'pieces_exportees': """
        SELECT eec.dossier, COUNT(DISTINCT piece) as nb_pieces_exportees
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        INNER JOIN ediflux_cerfrancecantal.edi_ecriture_export eee ON eee.ecriture_fk = eec.id
        GROUP BY eec.dossier
        ORDER BY eec.dossier;
    """,
    
    'ecritures_exportees': """
        SELECT eec.dossier, COUNT(DISTINCT eec.id) as nb_ecritures_exportees
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        INNER JOIN ediflux_cerfrancecantal.edi_ecriture_export eee ON eee.ecriture_fk = eec.id
        GROUP BY eec.dossier
        ORDER BY eec.dossier;
    """,
    
    'pieces_non_exportees': """
        SELECT eec.dossier, COUNT(DISTINCT piece) as nb_pieces_a_traiter
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        WHERE eec.id NOT IN (SELECT ecriture_fk FROM ediflux_cerfrancecantal.edi_ecriture_export eee)
        GROUP BY eec.dossier
        ORDER BY nb_pieces_a_traiter DESC;
    """,
    
    'ecritures_non_exportees': """
        SELECT eec.dossier, COUNT(DISTINCT eec.id) as nb_ecritures_a_traiter
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        WHERE eec.id NOT IN (SELECT ecriture_fk FROM ediflux_cerfrancecantal.edi_ecriture_export eee)
        GROUP BY eec.dossier
        ORDER BY nb_ecritures_a_traiter DESC;
    """,
    
    'comptes_attente': """
        SELECT eec.dossier, COUNT(DISTINCT eec.id) as nb_comptes_attente
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        WHERE eec.id NOT IN (SELECT ecriture_fk FROM ediflux_cerfrancecantal.edi_ecriture_export eee)
        AND eec.code_comptable LIKE '47%'
        GROUP BY eec.dossier
        ORDER BY nb_comptes_attente DESC;
    """,
    
    'dates_extremes': """
        SELECT 
            eec.dossier, 
            TO_CHAR(MIN(eec.date), 'DD-MM-YYYY') as date_min_a_traiter,
            TO_CHAR(MAX(eec.date), 'DD-MM-YYYY') as date_max_a_traiter
        FROM ediflux_cerfrancecantal.edi_ecriture_comptable eec
        WHERE eec.id NOT IN (SELECT ecriture_fk FROM ediflux_cerfrancecantal.edi_ecriture_export eee)
        AND eec.code_comptable LIKE '47%'
        GROUP BY eec.dossier
        ORDER BY eec.dossier;
    """
}

def connect_database():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion à la base de données: {e}")
        return None

def execute_query(conn, query_name, query):
    """Execute a SQL query and return DataFrame"""
    try:
        df = pd.read_sql_query(query, conn)
        print(f"✅ {query_name}: {len(df)} lignes récupérées")
        return df
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution de {query_name}: {e}")
        return pd.DataFrame()

def merge_dataframes(dataframes):
    """Merge all dataframes on dossier column"""
    if not dataframes:
        return pd.DataFrame()
    
    # Start with the first dataframe
    result = dataframes[0].copy()
    
    # Merge with all other dataframes
    for df in dataframes[1:]:
        result = pd.merge(result, df, on='dossier', how='outer')
    
    # Fill NaN values with 0 for numeric columns
    numeric_columns = result.select_dtypes(include=['number']).columns
    result[numeric_columns] = result[numeric_columns].fillna(0)
    
    # Fill NaN values with empty string for other columns
    result = result.fillna('')
    
    return result

def generate_html_report(df, output_file):
    """Generate HTML report"""
    
    # Calculate totals
    totals = {}
    for col in df.select_dtypes(include=['number']).columns:
        totals[col] = df[col].sum()
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tableau de Bord KPI - Export EDI</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .summary-cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .card h3 {{
                margin: 0 0 10px 0;
                color: #333;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .card .number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin: 0;
            }}
            .table-container {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }}
            th {{
                background: #667eea;
                color: white;
                padding: 15px 10px;
                text-align: left;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 12px;
            }}
            td {{
                padding: 12px 10px;
                border-bottom: 1px solid #eee;
            }}
            tr:hover {{
                background-color: #f8f9ff;
            }}
            .number-cell {{
                text-align: right;
                font-weight: 600;
            }}
            .warning {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .good {{
                color: #27ae60;
                font-weight: bold;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 0.9em;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Tableau de Bord KPI</h1>
            <p>Export EDI - Suivi par Dossier</p>
            <p>Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
        </div>
        
        <div class="summary-cards">
            <div class="card">
                <h3>Total Dossiers</h3>
                <div class="number">{len(df)}</div>
            </div>
            <div class="card">
                <h3>Pièces à Traiter</h3>
                <div class="number">{int(totals.get('nb_pieces_a_traiter', 0))}</div>
            </div>
            <div class="card">
                <h3>Écritures à Traiter</h3>
                <div class="number">{int(totals.get('nb_ecritures_a_traiter', 0))}</div>
            </div>
            <div class="card">
                <h3>Comptes d'Attente</h3>
                <div class="number">{int(totals.get('nb_comptes_attente', 0))}</div>
            </div>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Dossier</th>
                        <th>Pièces Exportées</th>
                        <th>Écritures Exportées</th>
                        <th>Pièces à Traiter</th>
                        <th>Écritures à Traiter</th>
                        <th>Comptes d'Attente</th>
                        <th>Date Min</th>
                        <th>Date Max</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    # Add table rows
    for _, row in df.iterrows():
        pieces_a_traiter = int(row.get('nb_pieces_a_traiter', 0))
        comptes_attente = int(row.get('nb_comptes_attente', 0))
        
        # Apply warning/good classes based on values
        pieces_class = 'warning' if pieces_a_traiter > 50 else 'good' if pieces_a_traiter == 0 else ''
        comptes_class = 'warning' if comptes_attente > 10 else 'good' if comptes_attente == 0 else ''
        
        html_content += f"""
                    <tr>
                        <td><strong>{row['dossier']}</strong></td>
                        <td class="number-cell">{int(row.get('nb_pieces_exportees', 0))}</td>
                        <td class="number-cell">{int(row.get('nb_ecritures_exportees', 0))}</td>
                        <td class="number-cell {pieces_class}">{pieces_a_traiter}</td>
                        <td class="number-cell">{int(row.get('nb_ecritures_a_traiter', 0))}</td>
                        <td class="number-cell {comptes_class}">{comptes_attente}</td>
                        <td>{row.get('date_min_a_traiter', '')}</td>
                        <td>{row.get('date_max_a_traiter', '')}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>🔄 Ce rapport se met à jour automatiquement chaque jour</p>
            <p>📈 Les valeurs en rouge nécessitent une attention particulière</p>
        </div>
        
        <script>
            // Auto-refresh every hour
            setTimeout(function(){
                location.reload();
            }, 3600000);
        </script>
    </body>
    </html>
    """
    
    # Write HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Rapport HTML généré: {output_file}")

def main():
    """Main function"""
    print("🚀 Génération du tableau de bord KPI...")
    print("=" * 50)
    
    # Check if config file exists
    if not os.path.exists('config.txt'):
        print("❌ Fichier config.txt introuvable!")
        print("📝 Créez un fichier config.txt avec vos paramètres de base de données:")
        print("HOST=votre_serveur")
        print("DATABASE=votre_base")
        print("USER=votre_utilisateur") 
        print("PASSWORD=votre_mot_de_passe")
        print("PORT=5432")
        input("\n✋ Appuyez sur Entrée pour fermer...")
        return
    
    # Connect to database
    conn = connect_database()
    if not conn:
        input("\n✋ Appuyez sur Entrée pour fermer...")
        return
    
    try:
        # Execute all queries
        dataframes = []
        for query_name, query in QUERIES.items():
            df = execute_query(conn, query_name, query)
            if not df.empty:
                dataframes.append(df)
        
        # Merge all dataframes
        if dataframes:
            final_df = merge_dataframes(dataframes)
            final_df = final_df.sort_values('nb_pieces_a_traiter', ascending=False, na_position='last')
            
            # Generate HTML report
            output_file = f"kpi_dashboard_{date.today().strftime('%Y%m%d')}.html"
            generate_html_report(final_df, output_file)
            
            print("=" * 50)
            print(f"✅ Tableau de bord généré avec succès!")
            print(f"📁 Fichier: {output_file}")
            print(f"🌐 Le fichier va s'ouvrir automatiquement...")
            
            # Auto-open the HTML file
            import webbrowser
            webbrowser.open(output_file)
            
        else:
            print("❌ Aucune donnée récupérée")
            input("\n✋ Appuyez sur Entrée pour fermer...")
    
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        input("\n✋ Appuyez sur Entrée pour fermer...")
    
    finally:
        conn.close()
        
    print("\n🎉 Terminé! Le tableau de bord s'ouvre dans votre navigateur.")
    input("✋ Appuyez sur Entrée pour fermer...")

if __name__ == "__main__":
    main()