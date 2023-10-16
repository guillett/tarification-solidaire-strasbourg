import { useState, useEffect } from 'react'
import axios from 'axios'

import Details from '../components/details.js'

export const getStaticProps = async (context) => {
  const domain =
    process.env.NODE_ENV == 'production' ? '' : 'http://127.0.0.1:8000'
  const force = process.env.NODE_ENV !== 'production'
  return { props: { domain, force } }
}

function isOk(email, force) {
  return (
    force ||
    email?.endsWith('@strasbourg.eu') ||
    email === 'thomas@codeursenliberte.fr'
  )
}

export default function Home({ domain, force }) {
  const subjects = [
    { name: 'Culture - CCS', value: 'ccs' },
    { name: 'Mobilité', value: 'cts' },
    { name: 'Sports', value: 'sports' },
    { name: 'DEE', value: 'dee' },
    { name: 'Culture - CRR', value: 'crr' },
  ]
  const sources = [
    { name: 'CAF', value: 'caf' },
    { name: 'INSEE', value: 'insee' },
  ]
  const adjustments = [
    {
      name: 'pas d’ajustement',
      value: 'v1',
    },
    {
      name: '+1 part',
      value: 'v2',
    },
    {
      name: '+0.5 part',
      value: 'v3',
    },
    {
      name: '+0.25 part',
      value: 'v4',
    },
  ]
  const [email, setEmail] = useState()
  const [subject, setSubject] = useState(subjects[0].value)
  const [source, setSource] = useState(sources[0].value)
  const [adjustment, setadjustment] = useState(adjustments[0].value)
  const [error, setError] = useState()
  useEffect(() => {
    axios
      .get(`${domain}/me`)
      .then((res) => res.data)
      .then((info) => {
        if (info.email) {
          setEmail(info.email)
        }
      })
      .catch((e) => {})
  }, [domain])

  useEffect(() => {
    if (subject == 'dee' && source == 'insee') {
      setError('Les données INSEE ne peuvent pas être utilisée pour la DEE.')
    } else {
      setError()
    }
  })

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-2">
      <h1>Tarification solidaire de Strasbourg</h1>
      <h2>Outil d’évaluation budgétaire</h2>
      {isOk(email, force) && (
        <div>
          <form
            method="post"
            encType="multipart/form-data"
            action={`${domain}/template`}
          >
            <fieldset>
              <legend>
                1. Récupérez un fichier de barèmes pour votre direction.
              </legend>
              <div>
                <p></p>
                <label htmlFor="subject_get_bareme">Thématique : </label>
                <select name="subject" id="subject_get_bareme">
                  {subjects.map((subject) => (
                    <option key={subject.value} value={subject.value}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit">Obtenir un fichier de barèmes</button>
            </fieldset>
          </form>
          <fieldset>
            <legend>2. Modifiez le fichier Excel.</legend>
            <p>
              Le fichier Excel permet d’évaluer plusieurs scénarios en
              parallèle. Chaque onglet correspond à un scénario.
            </p>
            <p>
              Un onglet du fichier Excel contient les différents barèmes de
              votre direction. La première colonne correspond aux niveaux de QF.
              La première ligne des colonnes suivantes les contient les noms de
              chaque barème. Les lignes suivantes contiennent, les montants à
              associer aux différentes tranches.
            </p>
            <p>
              Chaque barème contient au moins un montant associé au QF 0 €, cela
              signifie que ce montant s’applique à partir de 0 € de QF et
              jusqu’au QF de la tranche suivante exclu.
            </p>
          </fieldset>
          <form
            method="post"
            encType="multipart/form-data"
            action={`${domain}/budget`}
          >
            <fieldset>
              <legend>
                3. Lancez l’évaluation budgétaire en renvoyant le fichier Excel.
              </legend>
              <div>
                <label htmlFor="file">Fichier de barèmes : </label>
                <input
                  name="file"
                  id="file"
                  type="file"
                  accept=".ods, application/vnd.oasis.opendocument.spreadsheet"
                />
              </div>
              <div>
                <label htmlFor="subject_get_budget">Thématique : </label>
                <select
                  name="subject"
                  id="subject_get_budget"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                >
                  {subjects.map((subject) => (
                    <option key={subject.value} value={subject.value}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="source_get_budget">Données : </label>
                <select
                  name="source"
                  id="source_get_budget"
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                >
                  {sources.map((source) => (
                    <option key={source.value} value={source.value}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="adjustment_get_budget">
                  Ajustement du QF EMS pour les personnes isolées (avec ou sans
                  enfant) :{' '}
                </label>
                <select
                  name="adjustment"
                  id="adjustment_get_budget"
                  value={adjustment}
                  onChange={(e) => setadjustment(e.target.value)}
                >
                  {adjustments.map((adjustment) => (
                    <option key={adjustment.value} value={adjustment.value}>
                      {adjustment.name}
                    </option>
                  ))}
                </select>
              </div>
              {error && <div className="warning">{error}</div>}
              <button type="submit" disabled={error}>
                Évaluer les scénarios
              </button>
            </fieldset>
          </form>
          <p>
            4. Récupérez et analysez les estimations de recettes pour chaque
            scénario et chaque service payant.
          </p>
          <div>
            <a href={`${domain}/logout`}>Se déconnecter</a>
          </div>
          <Details domain={domain} />
        </div>
      )}

      {!isOk(email, force) && (
        <div>
          <p>
            Cette application nécessite une authentification avec une adresse
            email de Strasbourg.
          </p>
          {email && (
            <div>
              <p>Adresse email utilisée : {email}</p>
              <a href={`${domain}/logout`}>Se déconnecter</a>
            </div>
          )}
          {!email && (
            <a href={`${domain}/login`}>
              <div className="moncomptepro-button" />
            </a>
          )}
          <div>
            <p>
              <a
                href="https://moncomptepro.beta.gouv.fr/"
                target="_blank"
                rel="noopener noreferrer"
                title="Qu’est-ce que MonComptePro ? - nouvelle fenêtre"
              >
                Qu’est-ce que MonComptePro ?
              </a>
            </p>
          </div>
        </div>
      )}
    </main>
  )
}
