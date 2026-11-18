/**
 * JÀPP – gestion automatique (SECOTRAMI)
 * Base de données : ce Google Sheets. API : application web Apps Script.
 * 1) Exécuter setup() une fois.  2) Déployer > Nouveau déploiement > Application web
 *    (Exécuter en tant que : moi ; Accès : tout le monde).
 */
var SHEET_ID = '16F1aH6F15cjY4GmIuGYta7yUKnPhHmuCCMWpYvs7apU';
var TABS = {
  cond: ['Date', 'ID', 'Prénom et nom', 'Téléphone', 'Voiture', 'Plaque', 'Places', 'Départ matin', 'Retour soir',
         'Passe par', 'Vérifié', 'Actif', 'Point de RDV', 'Prix (F)', 'Notes', 'Départ (ville, quartier)', 'Destination', 'Jours'],
  pass: ['Date', 'ID', 'Prénom et nom', 'Téléphone', 'Sens', 'Heure', 'Jours', 'Départ', 'Arrivée', 'Vérifié', 'Notes'],
  resa: ['Date', 'Réf', 'Trajet', 'Jour du trajet', 'Heure', 'Sens', 'Conducteur', 'Passager', 'Téléphone',
         'Statut', 'Payé', 'Montant (F)', 'Part SECOTRAMI (F)']
};
var NAMES = { cond: 'Conducteurs', pass: 'Passagers', resa: 'Réservations', bord: 'Tableau de bord', regl: 'Réglages' };
var JOURS = ['dimanche', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi'];

function setup() {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  ss.setSpreadsheetTimeZone('Africa/Dakar');
  Object.keys(TABS).forEach(function (k) {
    var sh = ss.getSheetByName(NAMES[k]) || ss.insertSheet(NAMES[k]);
    sh.getRange(1, 1, 1, TABS[k].length).setValues([TABS[k]]).setFontWeight('bold')
      .setBackground('#0E2A47').setFontColor('#FFFFFF');
    sh.setFrozenRows(1);
  });
  var c = ss.getSheetByName(NAMES.cond), p = ss.getSheetByName(NAMES.pass), r = ss.getSheetByName(NAMES.resa);
  r.getRange('J2:J500').setDataValidation(SpreadsheetApp.newDataValidation()
    .requireValueInList(['Réservé', 'Présent', 'Absent', 'Annulé'], true).build());

  var g = ss.getSheetByName(NAMES.regl) || ss.insertSheet(NAMES.regl);
  g.getRange('A1:B5').setValues([
    ['Réglage', 'Valeur'],
    ['Prix par place (F)', 1000],
    ['Commission SECOTRAMI (ex. 0,1 = 10 %)', 0],
    ['E-mail des alertes', Session.getEffectiveUser().getEmail() || 'kaayxoolli@gmail.com'],
    ['Réservations ouvertes', true]
  ]);
  g.getRange('A1:B1').setFontWeight('bold');
  g.getRange('B5').insertCheckboxes().check();

  var b = ss.getSheetByName(NAMES.bord) || ss.insertSheet(NAMES.bord, 0);
  b.clear();
  b.getRange('A1').setValue('JÀPP – Tableau de bord').setFontSize(16).setFontWeight('bold');
  var rows = [
    ['Conducteurs inscrits', '=MAX(0,COUNTA(Conducteurs!B2:B))'],
    ['Conducteurs vérifiés', '=COUNTIF(Conducteurs!K2:K,TRUE)'],
    ['Conducteurs actifs', '=COUNTIFS(Conducteurs!K2:K,TRUE,Conducteurs!L2:L,TRUE)'],
    ['Passagers inscrits', '=MAX(0,COUNTA(Passagers!B2:B))'],
    ['Passagers vérifiés', '=COUNTIF(Passagers!J2:J,TRUE)'],
    ['Réservations (total)', '=COUNTIFS(Réservations!B2:B,"<>",Réservations!J2:J,"<>Annulé")'],
    ['Réservations cette semaine', '=COUNTIFS(Réservations!A2:A,">="&(TODAY()-WEEKDAY(TODAY(),2)+1),Réservations!J2:J,"<>Annulé")'],
    ['Trajets effectués (présent)', '=COUNTIF(Réservations!J2:J,"Présent")'],
    ['Absences', '=COUNTIF(Réservations!J2:J,"Absent")'],
    ['Argent encaissé (F)', '=SUMIFS(Réservations!L2:L,Réservations!K2:K,TRUE)'],
    ['Part SECOTRAMI (F)', '=SUMIFS(Réservations!M2:M,Réservations!K2:K,TRUE)'],
    ['Reste à encaisser (F)', '=SUMIFS(Réservations!L2:L,Réservations!K2:K,FALSE,Réservations!J2:J,"Présent")']
  ];
  b.getRange(3, 1, rows.length, 2).setValues(rows);
  b.getRange('A3:A' + (rows.length + 2)).setFontWeight('bold');
  b.getRange('D2').setValue('Réservations par conducteur').setFontWeight('bold');
  b.getRange('D3').setFormula('=IFERROR(QUERY(Réservations!G2:L,"select G, count(G), sum(L) where G is not null and J <> \'Annulé\' group by G label G \'Conducteur\', count(G) \'Places\', sum(L) \'Montant (F)\'",0),"Aucune réservation")');
  b.setColumnWidth(1, 240);
  var s1 = ss.getSheetByName('Feuille 1') || ss.getSheetByName('Sheet1');
  if (s1 && ss.getSheets().length > 1) ss.deleteSheet(s1);
}

/* ---------- API ---------- */
function out_(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}
function tel_(s) { var d = String(s || '').replace(/\D/g, ''); return d.slice(-9); }
function clean_(s, n) { return String(s == null ? '' : s).replace(/[<>]/g, '').trim().slice(0, n || 120); }
function rows_(name) {
  var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(name);
  var v = sh.getDataRange().getValues(); v.shift(); return v;
}
function setting_(row) { return SpreadsheetApp.openById(SHEET_ID).getSheetByName(NAMES.regl).getRange('B' + row).getValue(); }
function append_(name, row, cols) {
  var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(name);
  sh.appendRow(row);
  var n = sh.getLastRow();
  (cols || []).forEach(function (c) { sh.getRange(n, c).insertCheckboxes(); });
}
function nextId_(name, prefix) { return prefix + ('000' + (rows_(name).length + 1)).slice(-3); }
function alert_(subject, body) {
  var to = setting_(4);
  if (to) { try { MailApp.sendEmail(to, 'JÀPP – ' + subject, body); } catch (e) {} }
}
function dayKey_(d) { return Utilities.formatDate(d, 'Africa/Dakar', 'yyyy-MM-dd'); }

/** Prochains jours de trajet (7 jours, dimanche compris). */
function nextDays_() {
  var out = [], d = new Date();
  var hour = Number(Utilities.formatDate(d, 'Africa/Dakar', 'H'));
  if (hour >= 20) d = new Date(d.getTime() + 864e5);
  while (out.length < 7) {
    var wd = Number(Utilities.formatDate(d, 'Africa/Dakar', 'u')) % 7; // 1=lundi … 7=dimanche → 0
    out.push({ key: dayKey_(d), label: JOURS[wd] + ' ' + Utilities.formatDate(d, 'Africa/Dakar', 'd/MM') });
    d = new Date(d.getTime() + 864e5);
  }
  return out;
}

/** Trajets publiés : seulement les conducteurs vérifiés ET actifs, sans téléphone ni plaque. */
function trips_() {
  var prixDefaut = Number(setting_(2)) || 1000, list = [];
  rows_(NAMES.cond).forEach(function (c) {
    if (c[10] !== true || c[11] !== true) return;
    var prenom = String(c[2]).split(' ')[0], prix = Number(c[13]) || prixDefaut, places = Number(c[6]) || 1;
    var dep = String(c[15] || 'Départ à confirmer'), arr = String(c[16] || 'Destination à confirmer');
    var jd = String(c[17] || '').toLowerCase();
    if (c[7] && c[7] !== 'pas le matin') list.push({ id: c[1] + '-M', jd: jd, conducteur: prenom, voiture: c[4], places: places,
      heure: c[7], sens: dep + ' → ' + arr, depart: dep, arrivee: arr, rdv: c[12] || c[9] || 'à confirmer', prix: prix });
    if (c[8] && c[8] !== 'pas de retour' && c[8] !== 'pas le soir') list.push({ id: c[1] + '-S', jd: jd, conducteur: prenom, voiture: c[4], places: places,
      heure: c[8], sens: arr + ' → ' + dep, depart: arr, arrivee: dep, rdv: c[12] || 'à confirmer', prix: prix });
  });
  var taken = {};
  rows_(NAMES.resa).forEach(function (r) {
    if (!r[2] || r[9] === 'Annulé') return;
    var k = r[2] + '|' + (r[3] instanceof Date ? dayKey_(r[3]) : String(r[3]));
    taken[k] = (taken[k] || 0) + 1;
  });
  var days = nextDays_();
  list.forEach(function (t) {
    t.jours = days.filter(function (d) { return !t.jd || t.jd.indexOf(d.label.split(' ')[0]) >= 0; }).map(function (d) {
      return { key: d.key, label: d.label, libres: Math.max(0, t.places - (taken[t.id + '|' + d.key] || 0)) };
    });
    delete t.jd;
  });
  return list.filter(function (t) { return t.jours.length; });
}

function doGet(e) {
  return out_({ ok: true, ouvert: setting_(5) === true, trajets: trips_() });
}

function doPost(e) {
  var lock = LockService.getScriptLock();
  try {
    lock.waitLock(10000);
    var b = JSON.parse(e.postData.contents || '{}');
    if (b.site) return out_({ ok: true }); // champ piège anti-robots
    var ss = SpreadsheetApp.openById(SHEET_ID), now = new Date();
    if (b.type === 'passager') {
      if (!clean_(b.nom) || tel_(b.tel).length !== 9) return out_({ ok: false, code: 'champs' });
      var id = nextId_(NAMES.pass, 'P');
      append_(NAMES.pass, [now, id, clean_(b.nom), tel_(b.tel), clean_(b.sens), clean_(b.heure),
        clean_(b.jours), clean_(b.lieu), clean_(b.arrivee), false, ''], [10]);
      alert_('nouveau passager ' + id, clean_(b.nom) + ' – ' + tel_(b.tel) + '\n' + clean_(b.sens) + ' ' + clean_(b.heure) + ' (' + clean_(b.jours) + ')\nÀ vérifier : pièce d\'identité et filiation.');
      return out_({ ok: true, id: id });
    }
    if (b.type === 'conducteur') {
      if (!clean_(b.nom) || tel_(b.tel).length !== 9 || !clean_(b.voiture)) return out_({ ok: false, code: 'champs' });
      var cid = nextId_(NAMES.cond, 'C');
      append_(NAMES.cond, [now, cid, clean_(b.nom), tel_(b.tel), clean_(b.voiture), '',
        Number(b.places) || 1, clean_(b.matin), clean_(b.soir), clean_(b.lieu), false, false, '', '', '', clean_(b.depart, 60), clean_(b.dest, 60), clean_(b.jours, 80)], [11, 12]);
      alert_('nouveau conducteur ' + cid, clean_(b.nom) + ' – ' + tel_(b.tel) + '\n' + clean_(b.depart) + ' → ' + clean_(b.dest) + '\n' + clean_(b.voiture) + ', ' + b.places + ' place(s)\nAller ' + clean_(b.matin) + ' / retour ' + clean_(b.soir) + ' (' + clean_(b.jours) + ')' + '\nÀ vérifier : pièce d\'identité, permis, carte grise, plaque.');
      return out_({ ok: true, id: cid });
    }
    if (b.type === 'reservation') {
      if (setting_(5) !== true) return out_({ ok: false, code: 'ferme' });
      var t = tel_(b.tel);
      var pas = rows_(NAMES.pass).filter(function (p) { return tel_(p[3]) === t; })[0];
      if (!pas) return out_({ ok: false, code: 'inconnu' });
      if (pas[9] !== true) return out_({ ok: false, code: 'non_verifie' });
      var trip = trips_().filter(function (x) { return x.id === b.trajet; })[0];
      if (!trip) return out_({ ok: false, code: 'trajet' });
      var day = trip.jours.filter(function (d) { return d.key === b.jour; })[0];
      if (!day) return out_({ ok: false, code: 'jour' });
      if (day.libres < 1) return out_({ ok: false, code: 'complet' });
      var dup = rows_(NAMES.resa).some(function (r) {
        return r[2] === trip.id && (r[3] instanceof Date ? dayKey_(r[3]) : String(r[3])) === day.key && tel_(r[8]) === t && r[9] !== 'Annulé';
      });
      if (dup) return out_({ ok: false, code: 'deja' });
      var ref = nextId_(NAMES.resa, 'R');
      append_(NAMES.resa, [now, ref, trip.id, day.key, trip.heure, trip.sens, trip.conducteur,
        pas[2], t, 'Réservé', false, trip.prix, Math.round(trip.prix * (Number(setting_(3)) || 0))], [11]);
      alert_('réservation ' + ref, pas[2] + ' (' + t + ') → trajet ' + trip.id + ' de ' + trip.conducteur + ', ' + day.label + ' à ' + trip.heure + '\n' + trip.sens + '\nEnvoie au passager la voiture et la plaque.');
      return out_({ ok: true, ref: ref, passager: String(pas[2]).split(' ')[0], jour: day.label, heure: trip.heure, conducteur: trip.conducteur, prix: trip.prix });
    }
    return out_({ ok: false, code: 'type' });
  } catch (err) {
    return out_({ ok: false, code: 'erreur' });
  } finally {
    try { lock.releaseLock(); } catch (e) {}
  }
}

/** Mise à jour des en-têtes (ajout Quartier de départ / Destination), sans toucher aux réglages. */
function majColonnes() {
  var sh = SpreadsheetApp.openById(SHEET_ID).getSheetByName(NAMES.cond);
  sh.getRange(1, 1, 1, TABS.cond.length).setValues([TABS.cond]).setFontWeight('bold')
    .setBackground('#0E2A47').setFontColor('#FFFFFF');
}
