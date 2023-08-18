from base_period import base_period

baremes = {
    "apl_1_2j": lambda p: p.communes.strasbourg.periscolaire_loisirs.demi_journee.bareme,
    "apl_j": lambda p: p.communes.strasbourg.periscolaire_loisirs.journee.bareme,
    "apm": lambda p: p.communes.strasbourg.periscolaire_maternelle.bareme,
    "dee_std": lambda p: p.metropoles.strasbourg.tarifs_cantine,
    "dee_veg": lambda p: p.metropoles.strasbourg.tarifs_repas_vege,
    "dee_pan": lambda p: p.metropoles.strasbourg.tarifs_repas_panier,
    "ccs_eveil_tp": lambda p: p.communes.strasbourg.centre_choregraphique.eveil.TP,
    "ccs_eveil_ra": lambda p: p.communes.strasbourg.centre_choregraphique.eveil.RA,
    "ccs_eveil_rb": lambda p: p.communes.strasbourg.centre_choregraphique.eveil.RB,
    "ccs_enf_1c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._1_cours.TP,
    "ccs_enf_1c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._1_cours.RA,
    "ccs_enf_1c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._1_cours.RB,
    "ccs_enf_2c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._2_cours.TP,
    "ccs_enf_2c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._2_cours.RA,
    "ccs_enf_2c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._2_cours.RB,
    "ccs_enf_3c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._3_cours.TP,
    "ccs_enf_3c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._3_cours.RA,
    "ccs_enf_3c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._3_cours.RB,
    "ccs_enf_4c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._4_cours.TP,
    "ccs_enf_4c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._4_cours.RA,
    "ccs_enf_4c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.enfant._4_cours.RB,
    "ccs_adu_1c_tri_tp": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours_trimestre.TP,
    "ccs_adu_1c_tri_ra": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours_trimestre.RA,
    "ccs_adu_1c_tri_rb": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours_trimestre.RB,
    "ccs_adu_1c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours.TP,
    "ccs_adu_1c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours.RA,
    "ccs_adu_1c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._1_cours.RB,
    "ccs_adu_2c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._2_cours.TP,
    "ccs_adu_2c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._2_cours.RA,
    "ccs_adu_2c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._2_cours.RB,
    "ccs_adu_3c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._3_cours.TP,
    "ccs_adu_3c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._3_cours.RA,
    "ccs_adu_3c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._3_cours.RB,
    "ccs_adu_4c_tp": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._4_cours.TP,
    "ccs_adu_4c_ra": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._4_cours.RA,
    "ccs_adu_4c_rb": lambda p: p.communes.strasbourg.centre_choregraphique.adulte._4_cours.RB,
    "cons_enf12_agent": lambda p: p.communes.strasbourg.conservatoire.traditionnel.agent_ems.enfant_12,
    "cons_enf12_ems": lambda p: p.communes.strasbourg.conservatoire.traditionnel.habitant_ems.enfant_12,
    "cons_enf12_ext": lambda p: p.communes.strasbourg.conservatoire.traditionnel.hors_ems.enfant_12,
    "cons_enf3": lambda p: p.communes.strasbourg.conservatoire.traditionnel.enfant_3,
    "cons_ha_ems_1": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.habitant_ems.enfant_1,
    "cons_ha_ext_1": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.hors_ems.enfant_1,
    "cons_ha_ems_2": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.habitant_ems.enfant_2,
    "cons_ha_ext_2": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.hors_ems.enfant_2,
    "cons_ha_ems_3": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.habitant_ems.enfant_3,
    "cons_ha_ext_3": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.hors_ems.enfant_3,
    "cons_ha_ems_4": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.habitant_ems.enfant_4,
    "cons_ha_ext_4": lambda p: p.communes.strasbourg.conservatoire.horaires_amenages.hors_ems.enfant_4,
    "cts_base": lambda p: p.metropoles.strasbourg.tarification_solidaire.bareme,
    "cts_reduit": lambda p: p.metropoles.strasbourg.tarification_solidaire.bareme_reduit,
    "cts_emeraude": lambda p: p.metropoles.strasbourg.tarification_solidaire.bareme_emeraude,
    "pat_pu": lambda p: p.communes.strasbourg.patinoire.entree_unitaire.bareme_qf,
    "pat_pu_reduit": lambda p: p.communes.strasbourg.patinoire.entree_unitaire.bareme_qf_reduit,
    "pat_10": lambda p: p.communes.strasbourg.patinoire._10_entrees.bareme_qf,
    "pat_10_reduit": lambda p: p.communes.strasbourg.patinoire._10_entrees.bareme_qf_reduit,
    "pat_5_ce": lambda p: p.communes.strasbourg.patinoire.ce.entrees,
    "pis_pu": lambda p: p.communes.strasbourg.piscine.entree_unitaire.bareme_qf,
    "pis_pu_reduit": lambda p: p.communes.strasbourg.piscine.entree_unitaire.bareme_qf_reduit,
    "pis_10": lambda p: p.communes.strasbourg.piscine._10_entrees.bareme_qf,
    "pis_10_reduit": lambda p: p.communes.strasbourg.piscine._10_entrees.bareme_qf_reduit,
    "pis_5ce": lambda p: p.communes.strasbourg.piscine.ce.entrees,
    "pis_abo_ann": lambda p: p.communes.strasbourg.piscine.abonnement_annuel.bareme,
    "pis_abo_ann_reduit": lambda p: p.communes.strasbourg.piscine.abonnement_annuel.bareme_reduit,
    "pis_abo_ann_ce": lambda p: p.communes.strasbourg.piscine.ce.abonnement,
    "pis_abo_ete": lambda p: p.communes.strasbourg.piscine.abonnement_ete,
    "pis_cycle": lambda p: p.communes.strasbourg.piscine.cycle.bareme,
    "pis_stage_ete": lambda p: p.communes.strasbourg.piscine.stage_ete.bareme,
    "pis_stage_vac": lambda p: p.communes.strasbourg.piscine.stage_vacances.bareme,
    "pis_stage_5s": lambda p: p.communes.strasbourg.piscine.stage_5_seances.bareme,
}


def build_table_data(tbs):
    p = tbs.get_parameters_at_instant(base_period)
    threshold_rows = {}
    for column in baremes:
        bareme = baremes[column](p)
        for index, level in enumerate(bareme.thresholds):
            if level not in threshold_rows:
                threshold_rows[level] = {"QF": level}
            threshold_rows[level][column] = bareme.amounts[index]

    level_data = [*threshold_rows.keys()]
    level_data.sort()

    columns = [{"id": "QF", "fields": {"type": "Numeric"}}]
    for b in baremes:
        columns.append({"id": b, "fields": {"type": "Numeric"}})

    records = [{"fields": threshold_rows[i]} for i in level_data]
    return columns, records
