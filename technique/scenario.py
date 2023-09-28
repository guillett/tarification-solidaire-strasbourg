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


class sslr(Variable):
    def formula(individu, period, parameters):
        return 0


class QfFiscalReform(Reform):
    def apply(self):
        self.update_variable(strasbourg_metropole_quotient_familial)
        self.update_variable(sslr)


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


class strasbourg_conservatoire_base_ressources(Variable):
    def formula(famille, period):
        return famille("qf_fiscal", period)


class CRRReform(Reform):
    def apply(self):
        self.update_variable(strasbourg_conservatoire_base_ressources)


class strasbourg_sports_reduit(Variable):
    def formula(individu, period):
        return (
            +(individu("age", period) <= 18)
            + (individu("taux_incapacite", period) >= 0.8)
            + individu.famille("agent_ems", period)
        )


class eurometropole_strasbourg_tarification_solidaire_transport_eligible_tarif_reduit(
    Variable
):
    def formula(individu, period):
        taux_incapacite = individu("taux_incapacite", period)
        return taux_incapacite >= 0.80


class StatutReform(Reform):
    def apply(self):
        self.update_variable(strasbourg_sports_reduit)
        self.update_variable(
            eurometropole_strasbourg_tarification_solidaire_transport_eligible_tarif_reduit
        )


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
        if sheet is not None:
            for i in range(1, sheet.ncols()):
                name = sheet[0, i].value
                if name is None:
                    continue
                brackets = []
                for j in range(1, sheet.nrows()):
                    qf = sheet[j, 0].value
                    if qf is None:
                        continue
                    amount = sheet[j, i].value
                    if amount is None:
                        continue
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


def process_file_sheets(tbs, subject, get_result_fnc, input_file, output_file):
    if input_file:
        n = 10
        doc = ezodf.opendoc(input_file)
        scenarios = [(s.name, s) for s in doc.sheets if not s.name.startswith('_')]
    else:
        n = 2
        scenarios = [("base", None)]

    res = []
    for name, sheet in scenarios:
        crr = CRRReform(tbs)
        fisc = QfFiscalReform(crr)
        sbr = SheetBasedReform(fisc, sheet)
        sbrr = StatutReform(sbr)
        reform = sbrr
        v = get_result_fnc(tbs, n, reform)
        res.append((name, v))

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

    if input_file:
        baremes_data = pd.read_excel(input_file, sheet_name=None)
        baremes = {}
        for n in baremes_data:
            b = baremes_data[n]
            if b.columns[0] != 'QF':
                continue

            c = []
            for column_name in b.columns:
                if column_name.startswith('Unnamed'):
                    break
                else:
                    c.append(column_name)

            nrows = b.QF[~b.QF.isna()].index.max()+1

            baremes[n] = pd.read_excel(input_file, sheet_name=n, usecols=c, nrows=nrows)
    else:
        baremes = {}

    file = pd.ExcelWriter(output_file)
    pd.concat(resumes, ignore_index=True).to_excel(file, sheet_name="Résumé")
    for i, (scenario, values) in enumerate(res):
        if subject != "cts":
            values[0].to_excel(file, sheet_name=scenario)

        def pf(d, pavant, papres):
            i = ["TYPOLOGIE", "prix_avant"]
            c = ["prix_apres"]
            groups = [*i, *c, "sample_id"]
            dn = d.rename(columns={pavant: "prix_avant", papres: "prix_apres"})
            dv = (
                dn.groupby(groups)
                .ajustement_mensuel_num.apply(len)
                .groupby(groups[:-1])
                .mean()
                .reset_index()
            )
            dr = dv.pivot(index=i, columns=c, values="ajustement_mensuel_num")
            dr.columns = pd.MultiIndex.from_tuples([('prix_apres', round(p, 2)) for p in dr.columns])

            dl = dr.reset_index()
            dl['prix_avant'] = dl['prix_avant'].round(2)
            return dl.set_index(['TYPOLOGIE', 'prix_avant'])

        if subject == "cts":
            pivot_count = pf(gdfs[i], "pu_calc", "pu_calc_r")
            pivot_count.to_excel(file, sheet_name=f"{scenario} tableau abonnements")
            pivot_sum = pf(gdfs[i], "pu_calc_ht", "pu_calc_ht_r")
            pivot_sum.to_excel(file, sheet_name=f"{scenario} tableau recettes")

        if scenario in baremes:
            baremes[scenario].to_excel(
                file, sheet_name=f"{scenario} barèmes", index=False
            )
        gdfs[i].to_pickle(f"{output_file}_{scenario}.pickle")

    file.close()
