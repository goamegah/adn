from graphviz import Digraph

dot = Digraph("intoxication_ethylique", format="png")
dot.attr(rankdir="TB", size="8,12")

# Nœud principal
dot.node("appel", "APPEL POUR INTOXICATION ÉTHYLIQUE", shape="box", style="filled", color="lightcoral")

# Étape 1 : Informations à recueillir
dot.node("infos", """• Horaire de la prise d’alcool
• Type d’alcool ingéré
• Volume d’alcool ingéré
• Recherche de prise de médicaments associée
• Recherche de signes de gravité :
  – neurologiques
  – respiratoires
  – cardiocirculatoires""",
         shape="box", style="rounded", color="black")

# Étape 2 : Arrêt cardiaque
dot.node("arret", "INCONSCIENT QUI NE RESPIRE PAS = ARRÊT CARDIAQUE", shape="box", color="red")

# Étape 3 : Situations possibles
dot.node("inconscient", "Patient inconscient\nou IMV associée", shape="box", color="red")
dot.node("conscient_asso", "Patient conscient\net intoxication éthylique isolée", shape="box", color="green")
dot.node("conscient_ou", "Patient conscient\nou intoxication éthylique isolée", shape="box", color="black")

# Étape 4 : Actions
dot.node("action_grave", """Proposition au médecin régulateur d’envoi d’un Premier Secours
Transfert de l’appel au médecin régulateur urgentiste""", shape="box", color="red")

dot.node("action_legere", """Transfert de l’appel au médecin régulateur généraliste""", shape="box", color="green")

# Liens
dot.edge("appel", "infos", label="Sécuriser l’appel", fontsize="10")
dot.edge("infos", "arret")
dot.edge("arret", "inconscient", color="red")
dot.edge("arret", "conscient_asso", color="green")
dot.edge("inconscient", "action_grave", color="red")
dot.edge("conscient_asso", "action_legere", color="green")

# Légende
dot.attr(label="""FIGURE — Arbre décisionnel : appel pour intoxication éthylique""",
         fontsize="10", color="black")

# Export
dot.render("intoxication_ethylique")
