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

period = "2022-01-01"


class StrasbourgSurveyScenario(AbstractSurveyScenario):
    def __init__(self, tbs, data=None):
        super(StrasbourgSurveyScenario, self).__init__()

        self.year = base_period
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


def new_bareme(bareme, threshold, amount):
    bareme.brackets = [
        parameters.ParameterScaleBracket(
            data={
                "threshold": {period: {"value": threshold}},
                "amount": {period: {"value": amount}},
            }
        )
    ]


class CEReform(Reform):
    def apply(self):
        def modify_ce_parameters(local_parameters):
            Ps = local_parameters.communes.strasbourg
            v_abo_ce = extract_max_value(Ps.piscine.abonnement_annuel.bareme)
            new_bareme(Ps.piscine.ce.abonnement, 0, v_abo_ce)

            v_10_entrees_piscine = extract_max_value(Ps.piscine._10_entrees.bareme_qf)
            new_bareme(Ps.piscine.ce.entrees, 0, v_10_entrees_piscine / 2)

            v_10_entrees_patinoire = extract_max_value(
                Ps.patinoire._10_entrees.bareme_qf
            )
            new_bareme(Ps.patinoire.ce.entrees, 0, v_10_entrees_patinoire / 2)

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
                (Pcts.bareme, [Pcts.bareme_reduit, Pcts.bareme_emeraude]),
                # Patinoire
                (
                    Ppat.entree_unitaire.bareme_qf,
                    [Ppat.entree_unitaire.bareme_qf_reduit],
                ),
                (Ppat._10_entrees.bareme_qf, [Ppat._10_entrees.bareme_qf_reduit]),
                # # Piscine
                (Ppis.abonnement_annuel.bareme, [Ppis.abonnement_annuel.bareme_reduit]),
                (
                    Ppis.entree_unitaire.bareme_qf,
                    [Ppis.entree_unitaire.bareme_qf_reduit],
                ),
                (Ppis._10_entrees.bareme_qf, [Ppis._10_entrees.bareme_qf_reduit]),
            ]
            for dest, origins in reductions:
                for origin in origins:
                    assert origin.brackets
                    assert dest.brackets
                    origin.brackets = dest.brackets

            return local_parameters

        self.modify_parameters(modifier_function=modify_ce_parameters)


class gristSimulationReform(Reform):
    def __init__(self, tbs):
        GRIST_DOC_ID = os.getenv("GRIST_DOC_ID")
        GRIST_API_KEY = os.getenv("GRIST_API_KEY")
        GRIST_SERVER = os.getenv("GRIST_SERVER")
        table_id = "Tableau_QF"
        self.levels = requests.get(
            f"{GRIST_SERVER}/api/docs/{GRIST_DOC_ID}/tables/{table_id}/records",
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
                        brackets.append(
                            parameters.ParameterScaleBracket(
                                data={
                                    "threshold": {period: {"value": r["fields"]["QF"]}},
                                    "amount": {period: {"value": r["fields"][b]}},
                                }
                            )
                        )
                bb = baremes[b](local_parameters)
                bb.brackets = brackets
            return local_parameters

        self.modify_parameters(modifier_function=modify_parameters_grist)
