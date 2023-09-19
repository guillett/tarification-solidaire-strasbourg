import { useState, useEffect } from 'react'
import axios from 'axios'

export const getStaticProps = async (context) => {
  const domain =
    process.env.NODE_ENV == 'production' ? '' : 'http://127.0.0.1:8000'
  return { props: { domain } }
}

function isOk(email) {
  return (
    email?.endsWith('@strasbourg.eu') || email === 'thomas@codeursenliberte.fr'
  )
}

export default function Home({ domain }) {
  const options = [
    { name: 'Culture - CCS', value: 'ccs' },
    /*    { name: 'Mobilité', value: 'cts' },
    { name: 'Sports', value: '' },
    { name: 'DEE', value: '' },
    { name: 'Culture - CRR', value: 'cons' },//*/
  ]
  const [email, setEmail] = useState('@strasbourg.eu')
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

  const test = (event) => {
    console.log(event)
  }
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-2">
      <h1>
        Application d’évaluation budgétaire dans le cadre de la refonte des
        grilles tarifaires de la Ville et l’Eurométropole de Strasbourg
      </h1>
      {isOk(email) && (
        <div>
          <form
            method="post"
            encType="multipart/form-data"
            action={`${domain}/budget`}
          >
            <fieldset>
              <legend>Évaluation budgétaire</legend>
              <div>
                <label htmlFor="file">Fichier de barèmes : </label>
                <input
                  name="file"
                  id="file"
                  type="file"
                  accept=".ods, application/vnd.oasis.opendocument.spreadsheet"
                  required
                  onChange={test}
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
          <form
            method="post"
            encType="multipart/form-data"
            action={`${domain}/template`}
          >
            <fieldset>
              <legend>Fichier de barèmes </legend>
              <div>
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
        </div>
      )}

      {!isOk(email) && (
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
