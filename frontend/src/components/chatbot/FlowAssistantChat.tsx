import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import axios from 'axios'
import { Send, Sparkles } from 'lucide-react'
import { generateBotFlow } from '@/services/deepseek'
import type { ChatAssistantMessage, CurrentFlowContext, GeneratedBotFlow } from '@/types'
import Button from '@/components/ui/Button'
import { cn } from '@/lib/cn'

interface Props {
  currentFlow: CurrentFlowContext | null
  onFlowGenerated: (flow: GeneratedBotFlow) => void
  disabled?: boolean
}

const INITIAL_MESSAGE: ChatAssistantMessage = {
  role: 'assistant',
  content:
    'Descreva o fluxo desejado. Para menu 1/2/3 use opções numeradas — o sistema cria nó Menu com ramificações. Exemplo: "Saudação com 1=funcionário, 2=parceiro, 3=outros; cada opção com mensagem diferente."',
}

export default function FlowAssistantChat({
  currentFlow,
  onFlowGenerated,
  disabled = false,
}: Props) {
  const [messages, setMessages] = useState<ChatAssistantMessage[]>([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [error, setError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const mutation = useMutation({
    mutationFn: (allMessages: ChatAssistantMessage[]) =>
      generateBotFlow(allMessages, currentFlow),
    onSuccess: (data) => {
      setError('')
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
      if (data.flow && data.applied) {
        onFlowGenerated(data.flow)
      } else if (data.reply && !data.applied) {
        setError('Fluxo não aplicado — veja a resposta da IA acima.')
      }
    },
    onError: (err: unknown) => {
      if (axios.isAxiosError(err)) {
        if (err.response?.status === 503) {
          setError('DeepSeek não conectado.')
          return
        }
        const detail = err.response?.data?.detail
        if (typeof detail === 'string') {
          setError(detail)
          return
        }
      }
      setError('Erro ao gerar fluxo. Tente novamente.')
    },
  })

  const handleSend = () => {
    const text = input.trim()
    if (!text || mutation.isPending || disabled) return

    const userMessage: ChatAssistantMessage = { role: 'user', content: text }
    const nextMessages = [...messages, userMessage]
    setMessages(nextMessages)
    setInput('')
    setError('')
    mutation.mutate(nextMessages)
  }

  return (
    <aside className="w-80 border-l border-wa-border flex flex-col shrink-0 bg-wa-panel/50">
      <div className="p-3 border-b border-wa-border flex items-center gap-2 shrink-0">
        <Sparkles className="w-4 h-4 text-wa-green shrink-0" />
        <div>
          <h3 className="text-sm font-semibold">Assistente IA</h3>
          <p className="text-[10px] text-wa-muted">DeepSeek gera o fluxo</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              'text-sm rounded-lg px-3 py-2 max-w-[95%] whitespace-pre-wrap',
              msg.role === 'user'
                ? 'ml-auto bg-wa-green/20 text-gray-100 border border-wa-green/30'
                : 'mr-auto bg-gray-800 text-gray-200 border border-wa-border',
            )}
          >
            {msg.content}
          </div>
        ))}
        {mutation.isPending && (
          <div className="text-sm text-wa-muted animate-pulse px-2">
            Gerando fluxo...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && (
        <div className="px-3 pb-2">
          <p className="text-xs text-red-400">{error}</p>
          {error.includes('não conectado') && (
            <Link to="/admin/deepseek" className="text-xs text-wa-green hover:underline">
              Configurar DeepSeek
            </Link>
          )}
        </div>
      )}

      <div className="p-3 border-t border-wa-border shrink-0">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Descreva o fluxo..."
            disabled={mutation.isPending || disabled}
            className="flex-1 px-3 py-2 text-sm bg-gray-800 border border-wa-border rounded-lg focus:outline-none focus:border-wa-green disabled:opacity-50"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || mutation.isPending || disabled}
            loading={mutation.isPending}
            className="px-3"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </aside>
  )
}
