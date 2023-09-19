import { useState, useEffect } from 'react'
import axios from 'axios'

function extractScenarios(columnNames) {
  return columnNames
    .filter((name) => {
      return (
        name != 'id' &&
        name != 'QF' &&
        name != 'QF_bis' &&
        !name.endsWith('_reduit')
      )
    })
    .map((name) => {
      return { name }
    })
}

export default function Home() {
  const [record, setRecord] = useState('Waiting for data..')
  const [records, setRecords] = useState('Waiting for data...')
  const [options, setOptions] = useState('Waiting for data...')

  const [scenarios, setScenarios] = useState([])
  const [scenario, setScenario] = useState(null)
  const [useFiscalQF, setUseFiscalQF] = useState(false)

  const [recettes, setRecettes] = useState(null)

  const [canSubmit, setCanSubmit] = useState(false)
  const [startFetchAt, setStartFetchAt] = useState(null)
  const [timer, setTimer] = useState(null)

  useEffect(() => {
    window.grist.ready()
    window.grist.onRecord((record) => {
      setRecord(Object.keys(record))
      if (true || !scenarios.length) {
        setScenarios(extractScenarios(Object.keys(record)))
      }
    })
    window.grist.onRecords((records) => {
      setRecords(JSON.stringify(records, null, 2))
      if (true || !scenarios.length) {
        setScenarios(extractScenarios(Object.keys(records[0])))
      }
    })
    window.grist.onOptions((options, interaction) =>
      setOptions(JSON.stringify({ options, interaction }, null, 2))
    )
  }, [scenarios.length])

  useEffect(() => {
    setCanSubmit(!startFetchAt && !!scenario)
  }, [scenario, startFetchAt])

  async function fetchResults() {
    const start = new Date()
    setStartFetchAt(start)
    const interval = setInterval(() => {
      const d = Math.round((new Date() - start) / 1000)
      setTimer(`(${d}s.)`)
    }, 100)
    try {
      const host =
        process.env.NODE_ENV === 'production' ? '' : 'http:localhost:5000'
      const url = `${host}/fetch?scenario=${scenario}&qf=${
        useFiscalQF ? 'fiscal' : 'caf'
      }`
      const response = await axios.get(url)
      const data = response.data
      setRecettes(data.table)
    } catch (e) {
      throw e
    } finally {
      setStartFetchAt(null)
      clearInterval(interval)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-2">
      <div dangerouslySetInnerHTML={{ __html: recettes }} />
      <div className="flex-col w-full max-w-5xl items-center justify-between font-mono text-sm">
        <h1 className="text-xl">Simulation</h1>
        <fieldset className="flex flex-col p-2">
          <legend className="text-lg">Scénario</legend>
          {scenarios.map((scenario) => (
            <label key={scenario.name}>
              <input
                type="radio"
                name="scenario"
                onChange={(e) => setScenario(e.target.value)}
                value={scenario.name}
              />{' '}
              {scenario.name}
            </label>
          ))}
        </fieldset>
        <div className="p-2">
          <label className="text-lg">
            <input
              type="checkbox"
              value={useFiscalQF}
              onChange={(e) => setUseFiscalQF(e.target.checked)}
            />{' '}
            QF Fiscal
          </label>
        </div>
        <button
          disabled={!canSubmit}
          className={`bg-blue-500 text-white font-bold py-2 px-4 rounded ${
            canSubmit ? 'hover:bg-blue-700' : 'opacity-50 cursor-not-allowed'
          }`}
          onClick={fetchResults}
        >
          Calculer {timer}
        </button>
      </div>
    </main>
  )
}
