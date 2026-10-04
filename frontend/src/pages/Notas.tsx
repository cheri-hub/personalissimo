import { ResourceManager } from '../components/ResourceManager'
import { NOTAS } from '../recursos'

export function Notas() {
  return (
    <main>
      <ResourceManager {...NOTAS} />
    </main>
  )
}
