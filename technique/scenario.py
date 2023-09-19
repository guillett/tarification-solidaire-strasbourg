from dotenv import load_dotenv

load_dotenv()

import os
import requests
import json

import pandas as pd
from openfisca_survey_manager.scenarios import AbstractSurveyScenario
from openfisca_core.model_api import Reform, Variable
from openfisca_core import parameters

from baremes import baremes
from base_period import base_period

period = "2023-01-01"


class StrasbourgSurveyScenario(AbstractSurveyScenario):
    def __init__(self, tbs, data=None, period=base_period):
        super(StrasbourgSurveyScenario, self).__init__()

        self.year = period
        self.non_neutralizable_variables = tbs.variables.keys()

        if "input_data_frame_by_entity" in data:
            dataframe_variables = set()
            for entity_dataframe in data["input_data_frame_by_entity"].values():
                if not isinstance(entity_dataframe, pd.DataFrame):
                    continue
                dataframe_variables = dataframe_variables.union(
                    set(entity_dataframe.columns)
                )
            self.used_as_input_variables = list(
                set(tbs.variables.keys()).intersection(dataframe_variables)
            )

        self.set_tax_benefit_systems(tbs)
        self.init_from_data(data=data)


class strasbourg_metropole_quotient_familial(Variable):
    def formula(famille, period):
        return famille("qf_fiscal", period)


class QfFiscalReform(Reform):
    def apply(self):
        self.update_variable(strasbourg_metropole_quotient_familial)


def extract_max_value(bareme):
    return max([max([v.value for v in b.amount.values_list]) for b in bareme.brackets])


def new_bracket(threshold, amount):
    return parameters.ParameterScaleBracket(
        data={
            "threshold": {period: {"value": threshold}},
            "amount": {period: {"value": amount}},
        }
    )


def new_single_value_bareme(bareme, amount):
    bareme.brackets = [new_bracket(0, amount)]


class CEReform(Reform):
    def apply(self):
        def modify_ce_parameters(local_parameters):
            Ps = local_parameters.communes.strasbourg
            v_abo_ce = extract_max_value(Ps.piscine.abonnement_annuel.bareme)
            new_single_value_bareme(Ps.piscine.ce.abonnement, v_abo_ce)

            v_10_entrees_piscine = extract_max_value(Ps.piscine._10_entrees.bareme_qf)
            new_single_value_bareme(Ps.piscine.ce.entrees, v_10_entrees_piscine / 2)

            v_10_entrees_patinoire = extract_max_value(
                Ps.patinoire._10_entrees.bareme_qf
            )
            new_single_value_bareme(Ps.patinoire.ce.entrees, v_10_entrees_patinoire / 2)

            return local_parameters

        self.modify_parameters(modifier_function=modify_ce_parameters)


class StatutReform(Reform):
    def apply(self):
        def modify_ce_parameters(local_parameters):
            Ps = local_parameters.communes.strasbourg
            Pccs = Ps.centre_choregraphique
            Pcons = Ps.conservatoire
            Pcts = local_parameters.metropoles.strasbourg.tarification_solidaire
            Ppat = Ps.patinoire
            Ppis = Ps.piscine
            reductions = [
                # CCS
                (Pccs.eveil.TP, [Pccs.eveil.RA, Pccs.eveil.RB]),
                (
                    Pccs.enfant._1_cours.TP,
                    [Pccs.enfant._1_cours.RA, Pccs.enfant._1_cours.RB],
                ),
                (
                    Pccs.enfant._2_cours.TP,
                    [Pccs.enfant._2_cours.RA, Pccs.enfant._2_cours.RB],
                ),
                (
                    Pccs.enfant._3_cours.TP,
                    [Pccs.enfant._3_cours.RA, Pccs.enfant._3_cours.RB],
                ),
                (
                    Pccs.enfant._4_cours.TP,
                    [Pccs.enfant._4_cours.RA, Pccs.enfant._4_cours.RB],
                ),
                (
                    Pccs.adulte._1_cours.TP,
                    [Pccs.adulte._1_cours.RA, Pccs.adulte._1_cours.RB],
                ),
                (
                    Pccs.adulte._2_cours.TP,
                    [Pccs.adulte._2_cours.RA, Pccs.adulte._2_cours.RB],
                ),
                (
                    Pccs.adulte._3_cours.TP,
                    [Pccs.adulte._3_cours.RA, Pccs.adulte._3_cours.RB],
                ),
                (
                    Pccs.adulte._4_cours.TP,
                    [Pccs.adulte._4_cours.RA, Pccs.adulte._4_cours.RB],
                ),
                (
                    Pccs.adulte._1_cours_trimestre.TP,
                    [
                        Pccs.adulte._1_cours_trimestre.RA,
                        Pccs.adulte._1_cours_trimestre.RB,
                    ],
                ),
                # Conservatoire
                (
                    Pcons.traditionnel.habitant_ems.enfant_12,
                    [Pcons.traditionnel.agent_ems.enfant_12],
                ),
                # CTS
                (
                    Pcts.bareme,
                    [
                        Pcts.bareme_reduit,
                        Pcts.bareme_emeraude,
                        Pcts.annuel.bareme,
                        Pcts.annuel.bareme_reduit,
                    ],
                ),
                # Patinoire
                (
                    Ppat.entree_unitaire.bareme_qf,
                    [Ppat.entree_unitaire.bareme_qf_reduit],
                ),
                (Ppat._10_entrees.bareme_qf, [Ppat._10_entrees.bareme_qf_reduit]),
                # Piscine
                (Ppis.abonnement_annuel.bareme, [Ppis.abonnement_annuel.bareme_reduit]),
                (
                    Ppis.entree_unitaire.bareme_qf,
                    [Ppis.entree_unitaire.bareme_qf_reduit],
                ),
                (Ppis._10_entrees.bareme_qf, [Ppis._10_entrees.bareme_qf_reduit]),
            ]
            for overrider, overridens in reductions:
                for overriden in overridens:
                    assert overriden.brackets
                    assert overrider.brackets
                    overriden.brackets = overrider.brackets

            return local_parameters

        self.modify_parameters(modifier_function=modify_ce_parameters)


class gristSimulationReform(Reform):
    def __init__(self, tbs):
        GRIST_DOC_ID = os.getenv("GRIST_DOC_ID")
        GRIST_API_KEY = os.getenv("GRIST_API_KEY")
        GRIST_SERVER = os.getenv("GRIST_SERVER")
        table_id = "Tableau_QF"
        self.levels = requests.get(
            f"{GRIST_SERVER}/api/docs/{GRIST_DOC_ID}/tables/{table_id}/records?sort=QF",
            headers={
                "Authorization": f"Bearer {GRIST_API_KEY}",
            },
        ).json()["records"]
        super().__init__(tbs)

    def apply(self):
        def modify_parameters_grist(local_parameters):
            for b in baremes:
                brackets = []
                for r in self.levels:
                    if b in r["fields"] and r["fields"][b] is not None:
                        brackets.append(new_bracket(r["fields"]["QF"], r["fields"][b]))
                bb = baremes[b](local_parameters)
                bb.brackets = brackets
            return local_parameters

        self.modify_parameters(modifier_function=modify_parameters_grist)


class SheetBasedReform(Reform):
    def __init__(self, tbs, sheet):
        self.scales = {}
        for i in range(1, sheet.ncols()):
            name = sheet[0, i].value
            brackets = []
            for j in range(1, sheet.nrows()):
                qf = sheet[j, 0].value
                amount = sheet[j, i].value
                brackets.append(new_bracket(qf, amount))
            self.scales[name] = brackets
        super().__init__(tbs)

    def apply(self):
        def modify_parameters_grist(local_parameters):
            for b in baremes:
                if b in self.scales:
                    brackets = self.scales[b]
                    bb = baremes[b](local_parameters)
                    bb.brackets = brackets
            return local_parameters

        self.modify_parameters(modifier_function=modify_parameters_grist)


import ezodf


def process_file_sheets(tbs, get_result_fnc, input_file, output_file):
    doc = ezodf.opendoc(input_file)
    res = []
    for s in doc.sheets:
        sbr = SheetBasedReform(tbs, s)
        sbrr = StatutReform(sbr)
        v = get_result_fnc(tbs, 10, sbrr)
        res.append((s.name, v))

    resumes = []
    gdfs = []
    for scenario, values in res:
        dfs = values[1]
        for service, df in dfs:
            df["service"] = service
        gdf = pd.concat([df for (_, df) in dfs], ignore_index=True)
        gdfs.append(gdf)
        resume = (
            gdf.groupby("sample_id")[["prix", "prix_r"]]
            .sum()
            .agg(["count", "average", "median", "std"])
            .rename(
                columns={"prix": "Recettes actuelles", "prix_r": "Recette simulées"},
                index={
                    "count": "Nombre d'estimations",
                    "average": "Moyenne des recettes",
                    "median": "Médiane des recettes",
                    "std": "Écart-type des recettes",
                },
            )
            .transpose()
            .reset_index(names="Indicateurs")
        )
        resume.insert(loc=0, column="Scénario", value=scenario)
        resumes.append(resume)

    columns = [
        "service",
        "sample_id",
        "individu_id",
        "qf_caf",
        "qf_fiscal",
        "prix_input",
        "prix",
        "prix_r",
    ]
    file = pd.ExcelWriter(output_file)
    pd.concat(resumes, ignore_index=True).to_excel(file, sheet_name="Résumé")
    for i, (scenario, values) in enumerate(res):
        values[0].to_excel(file, sheet_name=scenario)
        gdfs[i][columns].to_excel(file, sheet_name=f"{scenario} détails")
    file.close()
