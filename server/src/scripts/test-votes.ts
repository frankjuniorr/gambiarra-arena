#!/usr/bin/env node
/**
 * Script para testar votação com múltiplos votantes simulados
 */

const SERVER_URL = process.env.SERVER_URL || 'http://localhost:3000';

async function testVotes() {
  console.log('🗳️  Testando sistema de votação...\n');

  // 1. Pegar sessão e rodada atual
  const sessionRes = await fetch(`${SERVER_URL}/session`);
  const session = await sessionRes.json();

  if (!session.rounds || session.rounds.length === 0) {
    console.error('❌ Nenhuma rodada encontrada!');
    process.exit(1);
  }

  const round = session.rounds[0];
  const participants = session.participants || [];

  console.log(`📝 Rodada: ${round.index}`);
  console.log(`👥 Participantes: ${participants.length}\n`);

  if (participants.length === 0) {
    console.error('❌ Nenhum participante encontrado!');
    process.exit(1);
  }

  // 2. Simular 10 votantes diferentes
  const numVoters = 10;

  for (let voterId = 1; voterId <= numVoters; voterId++) {
    console.log(`\n👤 Votante ${voterId}:`);

    for (const participant of participants) {
      // Voto aleatório entre 1-5
      const score = Math.floor(Math.random() * 5) + 1;

      try {
        const voteRes = await fetch(`${SERVER_URL}/votes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            // Simula IPs diferentes adicionando header
            'X-Forwarded-For': `192.168.1.${voterId}`
          },
          body: JSON.stringify({
            roundId: round.id,
            participantId: participant.id,
            score,
          }),
        });

        if (voteRes.ok) {
          console.log(`  ✅ ${participant.nickname}: ${score} ⭐`);
        } else {
          const error = await voteRes.text();
          console.log(`  ❌ ${participant.nickname}: Erro - ${error}`);
        }
      } catch (error) {
        console.error(`  ❌ ${participant.nickname}: ${error}`);
      }

      // Pequeno delay para não sobrecarregar
      await new Promise(resolve => setTimeout(resolve, 50));
    }
  }

  // 3. Mostrar placar final
  console.log('\n\n📊 PLACAR FINAL:\n');

  const scoreboardRes = await fetch(`${SERVER_URL}/scoreboard`);
  const scoreboard = await scoreboardRes.json();

  scoreboard.forEach((entry: any, index: number) => {
    const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '  ';
    console.log(`${medal} ${index + 1}º - ${entry.nickname}`);
    console.log(`   Votos: ${entry.votes} | Média: ${entry.avg_score.toFixed(2)} | Total: ${entry.total_score.toFixed(2)}`);
    console.log(`   Tokens: ${entry.tokens} | TPS: ${entry.tps_avg?.toFixed(2) || 'N/A'}\n`);
  });

  console.log('✨ Teste concluído!\n');
}

testVotes().catch(console.error);
