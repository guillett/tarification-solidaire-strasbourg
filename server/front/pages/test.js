export default function Test() {
  const v = process.env.NODE_ENV
  return (
    <main className="flex min-h-screen flex-col items-center p-2">
      <h1>Hello</h1>
      <p>{v}</p>
    </main>
  )
}
