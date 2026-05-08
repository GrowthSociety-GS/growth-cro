# Bloc 5 — Psycho /18 — Sources consolidées

> **Statut** : sources agrégées 2026-04-10. Base pour `bloc_5_psycho_v3.json`.
> **Méthodo** : identique Blocs 1-4 — 5 sources internes, jamais de tête.

---

## Source 1 — `skills/growth-site-generator/references/conversion_psychology.md`

Document de 2526 lignes couvrant les 6 principes de Cialdini + 10 biais cognitifs avec implémentations code.

### Extraction pour Bloc 5 :

**Cialdini 1.1 Réciprocité** → psy_06
- "Quand on reçoit quelque chose, on se sent obligé de rendre"
- Valeur AVANT demande : guide gratuit, calculateur, outil, échantillon
- Test éthique : "Est-ce que quelqu'un paierait pour ce gratuit ?"
- Intensité : Fort (SaaS B2B) / Subtil (E-commerce DTC) / Très subtil (Luxury)

**Cialdini 1.2 Engagement & Cohérence** → psy_06
- "Une fois qu'on a dit OUI petit, on s'engage à rester cohérent"
- Micro-commitments : quiz → rapport → consultation → achat
- Progressive disclosure : 3 champs visibles → +2 après first click
- Test éthique : "Ce micro-engagement aide l'utilisateur ou juste nous ?"

**Cialdini 1.4 Autorité** → psy_05
- "Si un expert le dit, ça doit être vrai"
- Signaux : certifications, founder pedigree, media mentions, endorsements
- Test éthique : "Peut-on vérifier ces credentials en 2 minutes ?"

**Cialdini 1.5 Rareté** → psy_01, psy_02
- "Ce qui est rare est précieux. Urgence psychologique."
- 3 types : rareté de places, rareté temporelle, rareté de prix
- Test éthique : "Si on arrête de mentir demain, la rareté disparaît ? → manipulation"
- JAMAIS de countdown fake, stock fictif, urgence permanente

**Biais 2.1 Ancrage** → psy_03
- "Le premier nombre = référence mentale"
- Prix barré, valeur perçue, comparaison quotidienne, effet leurre
- Combinaisons : Ancrage + Rareté, Ancrage + Cadrage, Ancrage + Decoy

**Biais 2.3 Aversion à la Perte** → psy_04
- "Perdre 10€ fait 2× plus mal que gagner 10€"
- Framing perte > framing gain : "vous perdez X€/mois" > "gagnez X€/mois"
- Risk reversal : garantie, essai gratuit, sans engagement

**Biais 2.4 Effet IKEA** → psy_02, psy_06
- "On valorise ce qu'on a contribué à créer"
- Configurateur, quiz personnalisé, rapport sur-mesure

---

## Source 2 — `skills/cro-auditor/references/audit_criteria.md` V1 critère 3.6

| Id V1 | Critère | Top | Critique |
|---|---|---|---|
| 3.6 | Urgence/rareté crédible | Urgence réelle vérifiable, placement non intrusif | Faux timer régénérant, stock fictif, urgence permanente |

→ Inspiré directement psy_01 (urgence crédible vs fake) et le killer psy_01_fake_urgency.

---

## Source 3 — `skills/cro-auditor/references/cro_principles.md`

**Section 1.2 Manque de Social Proof** :
- Hiérarchie d'efficacité 6 niveaux (vidéo > avis vérifiés > screenshots > stats > logos > badges)
- Impact : CVR -20-35% sans social proof
→ Nourrit psy_05 (profondeur des signaux d'autorité et preuve sociale)

**Section 1.3 Frictions dans le tunnel — Friction de confiance** :
- "Pas de garantie, données perso demandées trop tôt, absence RGPD"
→ Nourrit psy_04 (risk reversal, micro-réassurances)

---

## Source 4 — `playbook/bloc_2_sources.md` sections Notion

**Section 1b Preuves sociales** :
- 61% des clients lisent les avis avant d'acheter
- Probabilité × 2.7 si ≥ 5 avis
- Hiérarchie : Vidéo ★5 > Avis vérifiés ★5 > Screenshots ★4 > Chiffres ★4 > Logos ★3 > Badges ★2 > Anonyme ★1
→ Nourrit psy_05 (autorité = les signaux les plus forts de cette hiérarchie)

**Section 1c FAQ anti-doute** :
- "Arme de conversion anti-doute" — traite les objections bloquantes
→ Nourrit psy_04 (risk reversal via réponse aux objections)

---

## Source 5 — `skills/site-capture/scripts/native_capture.py` section 11 psychoSignals

Données déjà extractées automatiquement par le natif, disponibles dans `capture.json.psychoSignals` :

| Champ | Type | Critère cible |
|---|---|---|
| urgency_words | int (count) | psy_01 |
| has_countdown | bool | psy_01 |
| has_deadline | bool | psy_01 |
| scarcity_words | int (count) | psy_01, psy_02 |
| has_stock_indicator | bool | psy_01, psy_02 |
| user_count_mentions | int | psy_05 |
| media_mentions | int | psy_05 |
| award_mentions | int | psy_05 |
| certification_mentions | int | psy_05 |
| has_crossed_price | bool | psy_03 |
| has_discount_badge | bool | psy_03 |
| has_free_offer | bool | psy_03, psy_04, psy_06 |
| has_guarantee | bool | psy_03, psy_04 |
| loss_framing | int (count) | psy_04 |
| expert_mentions | int | psy_05 |
| has_press_logos | bool | psy_05 |

→ 100% des données nécessaires au scoring sont déjà extractées. Le scorer score_psycho.py consomme directement ces champs.

---

## Décisions de périmètre vs Bloc 2 Persuasion

| Aspect | Bloc 2 Persuasion | Bloc 5 Psycho |
|---|---|---|
| Focus | Qualité du MESSAGE (copy) | MÉCANISMES comportementaux |
| per_01 vs psy_03 | per_01 = benefits > features (traduction du copy) | psy_03 = ancrage prix/valeur (framing numérique) |
| per_04 vs psy_05 | per_04 = PRÉSENCE de preuves concrètes | psy_05 = CRÉDIBILITÉ et DIVERSITÉ de l'autorité |
| per_05 vs psy_05 | per_05 = qualité des testimonials (copy) | psy_05 = signaux d'autorité (expert, cert, media) |
| Urgence | Non couvert par Bloc 2 | psy_01 = urgence/rareté crédibilité |
| Ancrage | Non couvert par Bloc 2 | psy_03 = framing prix/valeur |
| Risk reversal | Non couvert par Bloc 2 | psy_04 = garantie, loss framing |
| Réciprocité | Non couvert par Bloc 2 | psy_06 = valeur gratuite, micro-engagements |
