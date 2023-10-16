import { useState, useEffect } from 'react'
import axios from 'axios'

export default function Details({ domain, force }) {
  const [files, setFiles] = useState([])

  useEffect(() => {
    axios
      .get(`${domain}/files`)
      .then((r) => {
        setFiles(r.data)
      })
      .catch((e) => {})
  }, [])

  return (
    files.length > 0 && (
      <div>
        <form method="post" action={`${domain}/files`}>
          <fieldset>
            <legend>Récupérez un fichier spécifique.</legend>
            <div>
              <label htmlFor="name_details">Nom : </label>
              <select name="name" id="name_details">
                {files.map((f) => (
                  <option key={f.name} value={f.name}>
                    {f.name} ({f.size}Mo)
                  </option>
                ))}
              </select>
            </div>
            <button type="submit">Obtenir le fichier</button>
          </fieldset>
        </form>
      </div>
    )
  )
}
