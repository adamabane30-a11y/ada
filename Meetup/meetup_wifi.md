# Meetup Wi-Fi — Capture et compréhension du 4-way handshake WPA2-Personal

## Introduction

Cette démonstration présente les principales étapes d'une analyse de sécurité Wi-Fi en laboratoire : préparation de l'interface, observation des échanges, capture du handshake, analyse des paquets, génération de mots de passe candidats et test hors ligne.

L'objectif est de comprendre le fonctionnement du protocole WPA2-Personal (PSK), ainsi que les conditions permettant d'évaluer la robustesse d'un mot de passe Wi-Fi.

Les manipulations de capture, de désauthentification et de test de mots de passe doivent être effectuées uniquement sur un réseau que l'on possède ou pour lequel on dispose d'une autorisation explicite.

---

## 1. Préparation de l'interface Wi-Fi

### 1.1. Identifier la carte Wi-Fi

```bash
lsusb
iw dev
```

**`lsusb`** affiche les périphériques USB détectés. Cette commande permet de vérifier que l'adaptateur Wi-Fi USB est reconnu.

**`iw dev`** affiche les interfaces Wi-Fi disponibles et leur configuration. Dans notre cas, le nom de l'interface utilisé dans le document est `wlxaca2135e7c0b`.

Le nom d'une interface peut varier selon le système, le pilote et la manière dont le périphérique est connecté.

### 1.2. Préparer le mode monitor

```bash
sudo airmon-ng check kill
sudo airmon-ng start [interface]
iw dev
```

- `sudo` exécute une commande avec les privilèges administrateur.
- `airmon-ng` est un outil de la suite Aircrack-ng permettant de faciliter l'activation du mode monitor.
- `check kill` recherche et arrête les processus susceptibles de perturber la capture, notamment certains services réseau.
- `start [interface]` demande l'activation du mode monitor sur l'interface spécifiée.
- `iw dev` permet de vérifier l'état obtenu.

Le **mode monitor** permet d'observer les trames Wi-Fi reçues sur le canal écouté sans que la carte ait besoin d'être associée au réseau.

À la différence du mode managed, utilisé habituellement pour se connecter à un point d'accès, le mode monitor sert principalement à l'observation et à l'analyse du trafic radio.

Attention : l'arrêt des processus réseau peut interrompre temporairement la connexion Wi-Fi du système.

---

## 2. Observation et capture du handshake

### 2.1. Découvrir les réseaux

```bash
sudo airodump-ng [interface]
```

`airodump-ng` observe les trames Wi-Fi et affiche les réseaux et les stations détectés.

Les principales colonnes sont :

- **BSSID** : adresse MAC identifiant le point d'accès.
- **PWR** : indication du niveau de signal reçu.
- **CH** : canal Wi-Fi utilisé.
- **ENC** : mécanisme de sécurité détecté, par exemple WPA2.
- **AUTH** : méthode d'authentification indiquée.
- **ESSID** : nom du réseau Wi-Fi.

Ces informations permettent de comprendre l'environnement radio et d'identifier le réseau de laboratoire.

### 2.2. Observer un point d'accès précis

```bash
sudo airodump-ng --bssid [MAC_PA] --channel [num] [interface]
```

- `--bssid [MAC_PA]` limite l'observation au point d'accès identifié par son adresse MAC.
- `--channel [num]` indique le canal sur lequel écouter.
- `[interface]` correspond à l'interface en mode monitor.

Le canal doit correspondre à celui du point d'accès. Une écoute sur le mauvais canal peut empêcher de recevoir les messages du handshake.

### 2.3. Enregistrer la capture

```bash
sudo airodump-ng --bssid [MAC_PA] --channel [num] -w handshake [interface]
```

L'option `-w handshake` définit le préfixe des fichiers de sortie. La capture est généralement enregistrée dans un fichier tel que `handshake-01.cap`.

Le but est d'enregistrer les trames nécessaires à l'analyse ultérieure.

Dans un laboratoire autorisé, une reconnexion du client peut permettre d'observer un nouvel échange d'authentification. Une désauthentification forcée peut également provoquer une reconnexion, mais elle perturbe la connectivité du client : elle ne doit pas être utilisée contre des réseaux ou des utilisateurs sans autorisation.

**Point important :** voir un réseau dans Airodump-ng ne signifie pas qu'un handshake a été capturé. Il faut vérifier que les messages nécessaires sont effectivement présents dans le fichier.

La désauthentification est un mécanisme du standard IEEE 802.11. Elle sert à signaler qu'une station ou un point d'accès met fin à l'état d'authentification Wi-Fi.

sudo : exécute l'outil avec les privilèges nécessaires.
aireplay-ng : outil Aircrack-ng permettant notamment d'injecter et de rejouer des trames Wi-Fi.

--deauth 1 : demande l'envoi d'une quantité limitée de trames de désauthentification, selon le comportement de l'outil.

-a [MAC_PA] : indique l'adresse MAC du point d'accès concerné.

-c [MAC_VICT] : indique l'adresse MAC de la station destinataire.

[interface] : désigne l'interface utilisée pour l'injection.

---

## 3. Comprendre le 4-way handshake WPA2-Personal

### 3.1. À quoi sert cet échange ?

Le 4-way handshake est une procédure de négociation cryptographique entre un point d'accès (AP) et un client Wi-Fi (station ou STA).

Il permet notamment :

1. de vérifier que les deux parties disposent des éléments nécessaires à la dérivation de clés communes ;
2. de confirmer l'intégrité des messages de négociation ;
3. de coordonner l'installation des clés de chiffrement ;
4. de mettre en place les conditions nécessaires aux communications protégées.

Il utilise des messages **EAPOL-Key**. Dans ce contexte, EAPOL signifie *Extensible Authentication Protocol over LAN*. Le handshake n'est pas constitué de quatre mots de passe ni de quatre échanges d'identifiants.

### 3.2. Les clés et les valeurs à connaître

**PSK — Pre-Shared Key**

Dans WPA2-Personal, le mot de passe est une phrase secrète partagée entre le point d'accès et les clients autorisés.

**PMK — Pairwise Master Key**

La PMK est la clé maîtresse utilisée pour dériver les clés de session. Dans le mode WPA2-Personal classique, elle est dérivée de la phrase secrète et du SSID. Pour une phrase secrète WPA2 classique, cette dérivation utilise PBKDF2-HMAC-SHA1 avec 4 096 itérations et produit une clé de 256 bits.

**ANonce et SNonce**

Ce sont deux valeurs aléatoires utilisées pendant le handshake :

- **ANonce** : nombre aléatoire généré par le point d'accès.
- **SNonce** : nombre aléatoire généré par le client.

Ils servent à distinguer la session en cours et entrent dans la dérivation de la clé de session.

**PTK — Pairwise Transient Key**

La PTK est dérivée à partir de la PMK, de l'ANonce, du SNonce et des adresses MAC du point d'accès et du client.

Elle contient plusieurs éléments cryptographiques, dont :

- **KCK** : clé utilisée pour calculer et vérifier le MIC des messages EAPOL-Key.
- **KEK** : clé utilisée pour protéger certaines clés transmises dans les messages.
- **TK** : clé temporelle utilisée pour protéger les données unicast, selon la suite cryptographique négociée.

**MIC — Message Integrity Code**

Le MIC est un code d'intégrité calculé sur le message avec une clé cryptographique appropriée. Il permet au destinataire de vérifier que le message n'a pas été modifié et qu'il est cohérent avec la clé partagée.

Le MIC n'est ni le mot de passe Wi-Fi, ni le nom d'une clé de chiffrement.

**GTK — Group Temporal Key**

La GTK sert à protéger le trafic de groupe, notamment certaines communications multicast et broadcast. Elle est distincte de la clé utilisée pour les communications unicast entre un client et le point d'accès.

### 3.3. Les quatre messages EAPOL

#### Message 1 — Point d'accès vers client

**Sens : AP → STA**

Le point d'accès envoie un premier message EAPOL-Key contenant notamment l'ANonce et un compteur de rejeu (*Replay Counter*).

Le client reçoit l'ANonce et le conserve pour calculer la PTK. Le compteur de rejeu contribue à empêcher l'acceptation de messages anciens ou répétés dans un contexte invalide.

À ce stade, le message 1 ne contient normalement pas de MIC calculé à partir de la PTK de cette session.

**À retenir :** le point d'accès fournit au client le premier nombre aléatoire nécessaire à la dérivation de la clé.

#### Message 2 — Client vers point d'accès

**Sens : STA → AP**

Le client génère son propre nombre aléatoire, le SNonce. Il dispose alors des éléments nécessaires pour dériver la PTK à partir de la PMK, des deux nonces et des adresses MAC.

Le client renvoie notamment :

- le SNonce ;
- un MIC calculé avec la clé d'intégrité dérivée ;
- les informations de sécurité négociées, notamment l'élément RSN dans le handshake WPA2 classique.

Le point d'accès peut à son tour dériver la PTK et vérifier le MIC reçu.

Si la vérification réussit, il dispose d'une preuve cryptographique que le client possède les éléments nécessaires à cette dérivation.

**À retenir :** le client répond au point d'accès et prouve qu'il peut calculer le MIC attendu sans envoyer directement le mot de passe.

#### Message 3 — Point d'accès vers client

**Sens : AP → STA**

Après avoir validé le message 2, le point d'accès renvoie un message EAPOL-Key contenant notamment un MIC valide et les informations de contrôle nécessaires à l'installation des clés.

Le message 3 contient généralement l'ANonce et des indicateurs qui demandent au client d'installer les clés négociées. Il peut aussi transporter la GTK, protégée par la KEK.

Le client vérifie notamment le MIC et les informations de l'échange avant de procéder à l'installation des clés conformément au protocole.

**À retenir :** le point d'accès confirme la validité de l'échange et demande au client d'installer les clés de sécurité.

#### Message 4 — Client vers point d'accès

**Sens : STA → AP**

Le client envoie le dernier message EAPOL-Key avec un MIC valide. Il confirme ainsi la réception du message précédent et l'achèvement de sa partie de la procédure d'installation.

Le point d'accès reçoit cette confirmation et peut terminer le handshake.

**À retenir :** le quatrième message permet aux deux parties de terminer la procédure et de poursuivre leurs communications protégées.

### 3.4. Tableau récapitulatif

| Message | Sens | Éléments importants | Fonction principale |
|---|---|---|---|
| M1 | AP → STA | ANonce, compteur de rejeu | Fournir le nonce du point d'accès |
| M2 | STA → AP | SNonce, MIC, informations RSN | Répondre et permettre la vérification du MIC |
| M3 | AP → STA | ANonce, MIC, indicateurs d'installation, GTK éventuellement protégée | Confirmer l'échange et demander l'installation des clés |
| M4 | STA → AP | MIC, indicateurs de contrôle | Confirmer la réception et l'achèvement de la procédure |

Les champs exacts peuvent varier selon la suite cryptographique et les options négociées. Le tableau décrit le handshake WPA2-Personal classique.

### 3.5. Pourquoi ce handshake est-il intéressant en audit ?

Dans un audit WPA2-Personal, une capture exploitable du handshake peut permettre d'effectuer un test de mots de passe hors ligne.

Le principe est le suivant :

1. Un outil utilise une capture contenant les éléments cryptographiques nécessaires.
2. Il prend un mot de passe candidat et dérive la PMK à partir du candidat et du SSID.
3. Il dérive la PTK à partir de cette PMK et des valeurs capturées.
4. Il calcule le MIC attendu et le compare à celui enregistré dans la capture.

Si le MIC calculé correspond au MIC observé, le candidat est considéré comme correct, sous réserve que la capture et les paramètres soient valides.

Ce processus ne consiste donc pas à lire le mot de passe dans les paquets. Il consiste à vérifier des hypothèses de mot de passe.

La qualité du mot de passe est déterminante : un mot de passe long, unique et imprévisible est beaucoup plus difficile à retrouver par essais hors ligne qu'un mot de passe court ou courant.

Enfin, la capture doit être suffisamment complète et contenir les éléments nécessaires au test. La présence d'un simple paquet EAPOL ne garantit pas que les données soient exploitables.

---

## 4. Analyse des paquets avec Wireshark

```bash
sudo wireshark
```

Cette commande lance Wireshark, un outil graphique d'analyse des paquets réseau. Selon la configuration du système, il est préférable d'utiliser les permissions de capture configurées pour Wireshark plutôt que de lancer systématiquement toute l'interface graphique en tant que root.

Pour cette démonstration, il est possible d'ouvrir directement le fichier `.cap` enregistré précédemment.

### Filtre EAPOL

```text
eapol
```

Ce filtre affiche les paquets EAPOL, dont les messages EAPOL-Key du handshake.

Il permet de repérer les échanges et d'examiner les champs des quatre messages.

### Filtre de désauthentification

```text
wlan.fc.type_subtype == 0x0c
```

Ce filtre affiche les trames Wi-Fi de désauthentification. Il ne filtre pas les messages du handshake : il sert à analyser les trames de désauthentification éventuellement présentes dans la capture.

Pour examiner les quatre messages, il faut revenir au filtre `eapol`.

Dans les détails d'un paquet, on peut notamment examiner :

- le sens de transmission ;
- le type de message EAPOL-Key ;
- le nonce ;
- le MIC ;
- le compteur de rejeu ;
- les indicateurs de contrôle des clés.

L'objectif est de relier les champs observés à leur fonction dans le handshake, plutôt que de se limiter à constater la présence de quatre paquets.

---

## 5. Création d'une wordlist

```bash
python3 fxwordlist.py -m optimized -f Y -c 3 -d 3 -s 3 information.txt --merge ./annees.txt
```

Cette commande lance un script Python nommé `fxwordlist.py` pour produire une liste de mots de passe candidats à partir des informations fournies.


| Paramètre              | Signification                  | Effet                                                                                       |
| ---------------------- | ------------------------------ | ------------------------------------------------------------------------------------------- |
| `-m optimized`         | Mode de génération             | Choisit la stratégie `optimized` du script.                                                 |
| `-f Y`                 | Première lettre en majuscule   | Active cette transformation.                                                                |
| `-c 3`                 | Niveau d'ajout de caractères   | Active le niveau 3 des caractères supplémentaires définis par le script.                    |
| `-d 3`                 | Remplacements par des chiffres | Autorise jusqu'à trois remplacements selon la logique du programme.                         |
| `-s 3`                 | Remplacements par des symboles | Autorise jusqu'à trois remplacements selon la logique du programme.                         |
| `information.txt`      | Informations de départ         | Fournit les informations à transformer en candidats.                                        |
| `--merge ./annees.txt` | Fusion avec une wordlist       | Ajoute des combinaisons entre les informations générées et les entrées du fichier d'années. |

Pour compter les lignes d'un fichier :

```bash
wc -l wordlist.txt
```

- `wc` est un outil de comptage.
- `-l` compte les lignes.
- `wordlist.txt` est le fichier analysé.

Le résultat donne le nombre de lignes.

Une wordlist volumineuse n'est pas nécessairement efficace : sa pertinence dépend de la qualité des hypothèses et de la prévisibilité du mot de passe.

---

## 6. Conversion de la capture et test avec Hashcat

### 6.1. Conversion vers HC22000

```bash
hcxpcapngtool -o hash.hc22000 handshake.cap
```

- `hcxpcapngtool` traite les captures Wi-Fi et extrait les enregistrements compatibles avec certains outils de test de mots de passe.
- `-o hash.hc22000` définit le fichier de sortie.
- `handshake.cap` désigne la capture source.

Le format HC22000 est utilisé par Hashcat pour des données compatibles avec le mode 22000, qui couvre notamment les formats PMKID et EAPOL.

La conversion ne garantit pas qu'un enregistrement exploitable soit présent. Il faut vérifier le résultat produit par l'outil.

### 6.2. Examiner les périphériques de calcul

```bash
hashcat -I
hashcat -d 1 -m 22000 hash.hc22000 wordlist.txt --potfile-disable
```

L'option `-I` affiche les informations sur les plateformes et les périphériques de calcul détectés, notamment via OpenCL.

Cette étape permet de vérifier si Hashcat détecte correctement le matériel disponible.

### 6.3. Comprendre le test hors ligne

La commande de test utilise le mode 22000 de Hashcat. Elle compare des mots de passe candidats aux données cryptographiques extraites de la capture.

L'option `-m 22000` sélectionne le format de données. L'option `-d 1` sélectionne un périphérique de calcul selon l'identifiant indiqué par Hashcat. `--potfile-disable` désactive l'utilisation du fichier potfile pour cette exécution.

Un résultat négatif ne prouve pas que le réseau est invulnérable. Il peut signifier que le bon mot de passe ne figure pas parmi les candidats, que la capture est inexploitable ou que les données attendues sont absentes.

Cette étape illustre donc l'importance d'un mot de passe robuste face aux essais hors ligne.

### Pourquoi Hashcat est plus rapide qu’Aircrack-ng ?

Aircrack-ng et Hashcat peuvent tous les deux tester des mots de passe candidats, mais ils n’utilisent pas nécessairement les mêmes ressources matérielles.

- Aircrack-ng utilise principalement le CPU pour tester les candidats, avec des optimisations possibles selon le processeur.
- Hashcat est conçu pour exploiter massivement le parallélisme des GPU, qui peuvent effectuer un très grand nombre d’opérations en parallèle.

Un GPU peut donc tester beaucoup plus de candidats par seconde qu’un CPU dans les calculs adaptés à son architecture. Cependant, les performances réelles dépendent du matériel, de l’algorithme utilisé et de la configuration.

---


## 7. Retour au mode managed

Après la démonstration, l'interface peut être remise en mode managed afin de retrouver son utilisation habituelle comme client Wi-Fi.

```bash
sudo ip link set [interface] down
sudo iw dev [interface] set type managed
sudo ip link set [interface] up
```

- `ip link set ... down` désactive temporairement l'interface.
- `iw dev ... set type managed` sélectionne le mode client Wi-Fi classique.
- `ip link set ... up` réactive l'interface.

Il faut remplacer `[interface]` par le nom réel de l'interface concernée. Si le nom a changé lors de l'activation du mode monitor, il faut le vérifier avec `iw dev`.

Le document initial propose également :

```bash
sudo systemctl restart avahi-daemon
sudo systemctl restart NetworkManager
sudo systemctl restart wpa_supplicant
```

`systemctl restart` redémarre le service indiqué.

- `avahi-daemon` gère la découverte de services sur le réseau local ;
- `NetworkManager` gère les connexions réseau ;
- `wpa_supplicant` participe à la connexion et à l'authentification Wi-Fi.

Ces redémarrages ne sont pas systématiquement nécessaires. Ils dépendent de la configuration du système et peuvent interrompre temporairement les connexions. Il est préférable de vérifier l'état de l'interface et les services effectivement utilisés avant de les redémarrer.

---

## Conclusion

Cette démonstration montre qu'un audit Wi-Fi ne se limite pas à capturer des paquets. Il faut comprendre le fonctionnement du protocole, savoir reconnaître les messages EAPOL, vérifier la qualité de la capture et interpréter correctement les résultats du test hors ligne.

Le point central est le 4-way handshake : l'ANonce et le SNonce participent à la dérivation de la PTK ; le MIC permet de vérifier l'intégrité et l'authenticité des messages ; les derniers échanges coordonnent l'installation des clés.

La capture ne révèle pas directement le mot de passe. Elle peut cependant fournir les éléments nécessaires pour vérifier des mots de passe candidats hors ligne. C'est pourquoi un mot de passe WPA2-Personal long, unique et difficile à deviner demeure une protection essentielle.

L'objectif du meetup est donc de relier les observations réalisées dans les outils aux mécanismes cryptographiques qui assurent réellement la sécurité du réseau Wi-Fi.
