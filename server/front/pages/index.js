import { useState, useEffect } from 'react'
import axios from 'axios'

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
  const options = [
    { name: 'Culture - CCS', value: 'ccs' },
    { name: 'Mobilité', value: 'cts' },
    { name: 'Sports', value: 'sports' },
    { name: 'DEE', value: 'dee' },
    { name: 'Culture - CRR', value: 'crr' },
  ]
  const [email, setEmail] = useState()
  const [subject, setSubject] = useState()
  useEffect(() => {
    axios
      .get(`${domain}/me`)
      .then((res) => res.data)
      .then((info) => {
        if (info.email) {
          setEmail(info.email)
        }
      })
  }, [domain])

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
                <label htmlFor="subject">Thématique : </label>
                <select name="subject" id="subject">
                  {options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.name}
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
              Le fichier Excel permet d'évaluer plusieurs scénarios en
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
              signifie que ce montant s'applique à partir de 0 € de QF et
              jusqu'au QF de la tranche suivante exclu.
            </p>
          </fieldset>
          <form
            method="post"
            encType="multipart/form-data"
            action={`${domain}/budget`}
          >
            <fieldset>
              <legend>
                3. Lancez l'évaluation budgétaire en renvoyant le fichier Excel.
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
                <label htmlFor="subject">Thématique : </label>
                <select name="subject" id="subject" value={subject}>
                  {options.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.name}
                    </option>
                  ))}
                </select>
              </div>
              <button type="submit">Évaluer les scénarios</button>
            </fieldset>
          </form>
          <p>
            4. Récupérez et analysez les estimations de recettes pour chaque
            scénario et chaque service payant.
          </p>
          <div>
            <a href={`${domain}/logout`}>Se déconnecter</a>
          </div>
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
