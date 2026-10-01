import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3

class OngletNomenclature(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        
        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="📚 Nomenclature & Données Techniques", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # --- CONTENEUR PRINCIPAL (Gauche: Tableau, Droite: Édition) ---
        self.conteneur = ctk.CTkFrame(self, fg_color="transparent")
        self.conteneur.pack(fill="both", expand=True)

        # ==========================================
        # PARTIE GAUCHE : RECHERCHE ET TABLEAU
        # ==========================================
        self.frame_gauche = ctk.CTkFrame(self.conteneur, fg_color=("gray95", "#1F2937"), corner_radius=10)
        self.frame_gauche.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Barre de recherche
        frame_recherche = ctk.CTkFrame(self.frame_gauche, fg_color="transparent")
        frame_recherche.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(frame_recherche, text="🔍 Rechercher :", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.entry_recherche = ctk.CTkEntry(frame_recherche, width=300, placeholder_text="Référence ou Désignation...")
        self.entry_recherche.pack(side="left", fill="x", expand=True)
        self.entry_recherche.bind("<KeyRelease>", self.filtrer_tableau)

        # Configuration du style du Treeview (Tableau)
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#374151" if ctk.get_appearance_mode() == "Dark" else "#F9FAFB",
                        foreground="white" if ctk.get_appearance_mode() == "Dark" else "black",
                        rowheight=30,
                        fieldbackground="#374151" if ctk.get_appearance_mode() == "Dark" else "#F9FAFB",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#3B82F6')])
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))

        # Tableau (Treeview)
        colonnes = ("ref", "desig", "matiere", "poids", "temps", "qte_obj", "qte_prod")
        self.tableau = ttk.Treeview(self.frame_gauche, columns=colonnes, show="headings", style="Treeview")
        
        self.tableau.heading("ref", text="Référence")
        self.tableau.heading("desig", text="Désignation")
        self.tableau.heading("matiere", text="Matière")
        self.tableau.heading("poids", text="Poids (g)")
        self.tableau.heading("temps", text="Temps (min)")
        self.tableau.heading("qte_obj", text="À Produire")
        self.tableau.heading("qte_prod", text="Déjà Produit")
        
        self.tableau.column("ref", width=120, anchor="center")
        self.tableau.column("desig", width=220)
        self.tableau.column("matiere", width=120, anchor="center")
        self.tableau.column("poids", width=80, anchor="center")
        self.tableau.column("temps", width=90, anchor="center")
        self.tableau.column("qte_obj", width=100, anchor="center")
        self.tableau.column("qte_prod", width=100, anchor="center")

        self.tableau.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tableau.bind("<<TreeviewSelect>>", self.sur_selection_ligne)

        # ==========================================
        # PARTIE DROITE : ÉDITION DES DONNÉES
        # ==========================================
        self.frame_droite = ctk.CTkFrame(self.conteneur, width=350, fg_color=("gray95", "#1F2937"), corner_radius=10)
        self.frame_droite.pack(side="right", fill="y")
        self.frame_droite.pack_propagate(False)

        ctk.CTkLabel(self.frame_droite, text="🛠️ Données Techniques", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Variable Référence (Lecture seule)
        self.var_ref = ctk.StringVar(value="Sélectionnez une pièce")
        ctk.CTkLabel(self.frame_droite, textvariable=self.var_ref, font=ctk.CTkFont(size=16, weight="bold"), text_color="#3B82F6").pack(pady=(0, 10))

        # Formulaire
        form_frame = ctk.CTkFrame(self.frame_droite, fg_color="transparent")
        form_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(form_frame, text="Désignation :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 0))
        self.entry_desig = ctk.CTkEntry(form_frame, placeholder_text="Nom de la pièce")
        self.entry_desig.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Matière / Résine :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 0))
        self.entry_matiere = ctk.CTkEntry(form_frame, placeholder_text="Ex: Résine Model V3")
        self.entry_matiere.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Grammage par pièce (g / mL) :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 0))
        self.entry_grammage = ctk.CTkEntry(form_frame, placeholder_text="Ex: 15.5")
        self.entry_grammage.pack(fill="x", pady=5)

        ctk.CTkLabel(form_frame, text="Temps d'impression unitaire (min) :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 0))
        self.entry_temps = ctk.CTkEntry(form_frame, placeholder_text="Ex: 45")
        self.entry_temps.pack(fill="x", pady=5)

        # Section Quantités (Éditable)
        qte_frame = ctk.CTkFrame(self.frame_droite, fg_color="#374151", corner_radius=8)
        qte_frame.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(qte_frame, text="📈 Gestion des Quantités", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(qte_frame, text="Quantité à produire (Objectif) :", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10)
        self.entry_qte_obj = ctk.CTkEntry(qte_frame, placeholder_text="À produire")
        self.entry_qte_obj.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(qte_frame, text="Quantité déjà produite :", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10)
        self.entry_qte_prod = ctk.CTkEntry(qte_frame, placeholder_text="Produit")
        self.entry_qte_prod.pack(fill="x", padx=10, pady=(0, 10))

        # Boutons d'action (Mettre à jour & Supprimer)
        actions_frame = ctk.CTkFrame(self.frame_droite, fg_color="transparent")
        actions_frame.pack(fill="x", padx=20, side="bottom", pady=15)

        self.btn_sauvegarder = ctk.CTkButton(actions_frame, text="💾 Mettre à jour", font=ctk.CTkFont(weight="bold"), height=40, fg_color="#10B981", hover_color="#059669", state="disabled", command=self.sauvegarder_donnees)
        self.btn_sauvegarder.pack(fill="x", pady=(0, 8))

        self.btn_supprimer = ctk.CTkButton(actions_frame, text="🗑️ Supprimer la référence", font=ctk.CTkFont(weight="bold"), height=40, fg_color="#EF4444", hover_color="#B91C1C", state="disabled", command=self.supprimer_reference)
        self.btn_supprimer.pack(fill="x")

        # NOUVEAU : Vérifier et mettre à jour la BDD automatiquement
        self.verifier_et_mettre_a_jour_bdd()

        # Chargement initial
        self.charger_donnees()

    # ==========================================
    # LOGIQUE BASE DE DONNÉES
    # ==========================================
    def verifier_et_mettre_a_jour_bdd(self):
        """Vérifie si la colonne quantite_produite existe, sinon la crée automatiquement."""
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                
                # Récupérer les informations sur les colonnes de la table
                cursor.execute("PRAGMA table_info(references_generees)")
                colonnes_existantes = [colonne[1] for colonne in cursor.fetchall()]
                
                # Ajouter quantite_produite si elle n'existe pas
                if "quantite_produite" not in colonnes_existantes:
                    cursor.execute("ALTER TABLE references_generees ADD COLUMN quantite_produite INTEGER DEFAULT 0")
                    conn.commit()
                    print("Mise à jour BDD : Colonne 'quantite_produite' ajoutée.")
                    
        except Exception as e:
            print(f"Erreur lors de la vérification de la BDD : {e}")

    def charger_donnees(self, filtre=""):
        for item in self.tableau.get_children():
            self.tableau.delete(item)

        filtre = filtre.lower().strip()
        
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                # On utilise 'quantite' pour l'objectif (À Produire) et 'quantite_produite' pour ce qui est fait
                cursor.execute("""
                    SELECT reference_complete, designation, consommable_lie, quantite_conso, temps_unitaire, quantite, quantite_produite 
                    FROM references_generees
                    WHERE type_production = '3D'
                    ORDER BY reference_complete DESC
                """)
                
                for row in cursor.fetchall():
                    ref, desig, matiere, poids, temps, qte_obj, qte_prod = row
                    desig = desig if desig else "Sans nom"
                    matiere = matiere if matiere else "-"
                    qte_obj = qte_obj if qte_obj is not None else 0
                    qte_prod = qte_prod if qte_prod is not None else 0
                    
                    if filtre:
                        if filtre not in ref.lower() and filtre not in desig.lower():
                            continue

                    self.tableau.insert("", "end", values=(ref, desig, matiere, f"{poids} g", f"{temps} min", qte_obj, qte_prod))
                    
        except Exception as e:
            print(f"Erreur chargement nomenclature: {e}")

    def filtrer_tableau(self, event=None):
        texte_recherche = self.entry_recherche.get()
        self.charger_donnees(filtre=texte_recherche)

    def sur_selection_ligne(self, event):
        selection = self.tableau.selection()
        if not selection:
            self.desactiver_edition()
            return
            
        item = self.tableau.item(selection[0])
        valeurs = item['values']
        
        ref = valeurs[0]
        desig = valeurs[1]
        matiere = valeurs[2] if valeurs[2] != "-" else ""
        poids = str(valeurs[3]).replace(" g", "")
        temps = str(valeurs[4]).replace(" min", "")
        qte_obj = valeurs[5]
        qte_prod = valeurs[6]

        self.var_ref.set(ref)
        
        self.entry_desig.delete(0, 'end')
        self.entry_desig.insert(0, desig)

        self.entry_matiere.delete(0, 'end')
        self.entry_matiere.insert(0, matiere)
        
        self.entry_grammage.delete(0, 'end')
        self.entry_grammage.insert(0, poids if poids != "0.0" and poids != "0" else "")
        
        self.entry_temps.delete(0, 'end')
        self.entry_temps.insert(0, temps if temps != "0" else "")
        
        self.entry_qte_obj.delete(0, 'end')
        self.entry_qte_obj.insert(0, str(qte_obj))
        
        self.entry_qte_prod.delete(0, 'end')
        self.entry_qte_prod.insert(0, str(qte_prod))
        
        self.btn_sauvegarder.configure(state="normal")
        self.btn_supprimer.configure(state="normal")

    def desactiver_edition(self):
        self.var_ref.set("Sélectionnez une pièce")
        self.entry_desig.delete(0, 'end')
        self.entry_matiere.delete(0, 'end')
        self.entry_grammage.delete(0, 'end')
        self.entry_temps.delete(0, 'end')
        self.entry_qte_obj.delete(0, 'end')
        self.entry_qte_prod.delete(0, 'end')
        self.btn_sauvegarder.configure(state="disabled")
        self.btn_supprimer.configure(state="disabled")

    def sauvegarder_donnees(self):
        ref = self.var_ref.get()
        if ref == "Sélectionnez une pièce":
            return
            
        nouvelle_desig = self.entry_desig.get().strip()
        matiere = self.entry_matiere.get().strip()
        poids_str = self.entry_grammage.get().strip().replace(',', '.')
        temps_str = self.entry_temps.get().strip()
        qte_obj_str = self.entry_qte_obj.get().strip()
        qte_prod_str = self.entry_qte_prod.get().strip()

        if not nouvelle_desig:
            messagebox.showerror("Erreur", "La désignation ne peut pas être vide.")
            return

        try:
            poids = float(poids_str) if poids_str else 0.0
            temps = int(temps_str) if temps_str else 0
            qte_obj = int(qte_obj_str) if qte_obj_str else 0
            qte_prod = int(qte_prod_str) if qte_prod_str else 0
        except ValueError:
            messagebox.showerror("Erreur", "Vérifiez vos saisies : les grammages doivent être décimaux, et les temps/quantités doivent être des entiers.")
            return

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE references_generees 
                    SET designation = ?, consommable_lie = ?, quantite_conso = ?, temps_unitaire = ?, quantite = ?, quantite_produite = ?
                    WHERE reference_complete = ? AND type_production = '3D'
                """, (nouvelle_desig, matiere, poids, temps, qte_obj, qte_prod, ref))
                conn.commit()
                
            messagebox.showinfo("Succès", f"Les données de {ref} ont été mises à jour.")
            
            filtre_actuel = self.entry_recherche.get()
            self.charger_donnees(filtre=filtre_actuel)
            
            # Resélectionner la ligne modifiée
            for child in self.tableau.get_children():
                if self.tableau.item(child)["values"][0] == ref:
                    self.tableau.selection_set(child)
                    break
                    
        except Exception as e:
            messagebox.showerror("Erreur BDD", str(e))

    def supprimer_reference(self):
        ref = self.var_ref.get()
        if ref == "Sélectionnez une pièce":
            return

        reponse = messagebox.askyesno("Confirmation de suppression", f"Êtes-vous sûr de vouloir supprimer définitivement la référence '{ref}' ?\nCette action est irréversible.")
        if reponse:
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM references_generees WHERE reference_complete = ? AND type_production = '3D'", (ref,))
                    conn.commit()
                
                messagebox.showinfo("Supprimé", f"La référence '{ref}' a été supprimée avec succès.")
                self.desactiver_edition()
                self.charger_donnees()
                
            except Exception as e:
                messagebox.showerror("Erreur BDD", str(e))