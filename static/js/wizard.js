// ========================================
// BRILHO NEGRO
// WIZARD.JS 2.0
// Controle do cadastro em etapas
// ========================================


// ========================================
// ESTADO
// ========================================

let etapaAtual = 1;
let precisaResponsavel = false;

const totalEtapas = 7;


// ========================================
// CONTROLE DAS ETAPAS
// ========================================

function mostrarEtapa(){

    const etapas = document.querySelectorAll(".etapa");

    // Se a página atual não possui o wizard,
    // simplesmente não faz nada.
    if(!etapas.length){
        return;
    }


    etapas.forEach((etapa,index)=>{

        if(index + 1 === etapaAtual){

            etapa.classList.remove("d-none");

        }else{

            etapa.classList.add("d-none");

        }

    });


    atualizarProgresso();

    atualizarBotoes();


    const numero = document.getElementById("numeroEtapa");

    if(numero){

        numero.innerHTML = etapaAtual;

    }


    if(etapaAtual === 7){

        montarResumo();

    }

}


// ========================================
// BARRA DE PROGRESSO
// ========================================

function atualizarProgresso(){

    const barra = document.getElementById("barraProgresso");

    if(!barra){
        return;
    }


    const progresso =
        ((etapaAtual - 1) / (totalEtapas - 1)) * 100;


    barra.style.width = progresso + "%";

}


// ========================================
// BOTÕES
// ========================================

function atualizarBotoes(){

    const anterior =
        document.getElementById("btnAnterior");

    const proximo =
        document.getElementById("btnProximo");


    if(anterior){

        anterior.style.display =
            etapaAtual === 1
                ? "none"
                : "block";

    }


    if(proximo){

        proximo.innerHTML =
            etapaAtual === totalEtapas
                ? "Enviar"
                : "Próximo →";

    }

}


// ========================================
// VALIDAÇÃO DAS ETAPAS
// ========================================

function validarEtapa(){

    const etapas =
        document.querySelectorAll(".etapa");


    // Página sem wizard
    if(!etapas.length){
        return true;
    }


    const etapa =
        etapas[etapaAtual - 1];


    if(!etapa){

        return true;

    }


    const campos =
        etapa.querySelectorAll(
            "input[required], select[required], textarea[required]"
        );


    for(let campo of campos){

        const valor =
            typeof campo.value === "string"
                ? campo.value.trim()
                : campo.value;


        if(
            valor === "" ||
            valor === "Selecione"
        ){

            campo.focus();

            campo.classList.add("is-invalid");

            return false;

        }


        campo.classList.remove("is-invalid");

    }


    return true;

}


// ========================================
// NAVEGAÇÃO
// ========================================

function proximaEtapa(){

    // Se não estiver na página do wizard,
    // não executa a lógica.
    const etapas =
        document.querySelectorAll(".etapa");

    if(!etapas.length){
        return;
    }


    // Antes de sair da etapa 5 verifica novamente a idade
    if(etapaAtual === 5){

        verificarIdade();

    }


    if(!validarEtapa()){

        return;

    }


    if(etapaAtual < totalEtapas){

        etapaAtual++;


        // Pula responsável somente se tiver certeza que é maior

        if(
            etapaAtual === 6 &&
            precisaResponsavel === false
        ){

            etapaAtual = 7;

        }


        mostrarEtapa();


    }else{

        const formulario =
            document.querySelector("form");

        if(formulario){

            formulario.submit();

        }

    }

}


// ========================================
// VOLTAR ETAPA
// ========================================

function voltarEtapa(){

    const etapas =
        document.querySelectorAll(".etapa");

    if(!etapas.length){
        return;
    }


    if(etapaAtual > 1){

        etapaAtual--;


        if(
            etapaAtual === 6 &&
            !precisaResponsavel
        ){

            etapaAtual--;

        }


        mostrarEtapa();

    }

}


// ========================================
// IR PARA ETAPA
// ========================================

function irParaEtapa(numero){

    const etapas =
        document.querySelectorAll(".etapa");

    if(!etapas.length){
        return;
    }


    if(
        numero >= 1 &&
        numero <= totalEtapas
    ){

        etapaAtual = numero;

        mostrarEtapa();

    }

}


// ========================================
// MÁSCARA TELEFONE
// ========================================

function formatarTelefone(campo){

    if(!campo){
        return;
    }


    let valor =
        campo.value.replace(/\D/g,'');


    if(valor.length > 11){

        valor =
            valor.substring(0,11);

    }


    if(valor.length > 6){

        valor =
            "(" +
            valor.substring(0,2) +
            ") " +
            valor.substring(2,7) +
            "-" +
            valor.substring(7);

    }
    else if(valor.length > 2){

        valor =
            "(" +
            valor.substring(0,2) +
            ") " +
            valor.substring(2);

    }


    campo.value = valor;

}


// ========================================
// MÁSCARA CPF
// ========================================

function formatarCPF(campo){

    if(!campo){
        return;
    }


    let valor =
        campo.value.replace(/\D/g,'');


    if(valor.length > 11){

        valor =
            valor.substring(0,11);

    }


    if(valor.length > 9){

        valor =
            valor.substring(0,3) + "." +
            valor.substring(3,6) + "." +
            valor.substring(6,9) + "-" +
            valor.substring(9);

    }
    else if(valor.length > 6){

        valor =
            valor.substring(0,3) + "." +
            valor.substring(3,6) + "." +
            valor.substring(6);

    }
    else if(valor.length > 3){

        valor =
            valor.substring(0,3) + "." +
            valor.substring(3);

    }


    campo.value = valor;

}


// ========================================
// MÁSCARA CEP
// ========================================

function formatarCEP(campo){

    if(!campo){
        return;
    }


    let valor =
        campo.value.replace(/\D/g,'');


    if(valor.length > 8){

        valor =
            valor.substring(0,8);

    }


    if(valor.length > 5){

        valor =
            valor.substring(0,5)
            +
            "-"
            +
            valor.substring(5);

    }


    campo.value = valor;

}


// ========================================
// BUSCA CEP
// ========================================

async function buscarCEP(){

    const campo =
        document.getElementById("cep");


    if(!campo){

        return;

    }


    let cep =
        campo.value.replace(/\D/g,'');


    if(cep.length !== 8){

        return;

    }


    try{

        const resposta =
            await fetch(
                "https://viacep.com.br/ws/" +
                cep +
                "/json/"
            );


        if(!resposta.ok){

            throw new Error(
                "Erro ao consultar o CEP."
            );

        }


        const dados =
            await resposta.json();


        if(dados.erro){

            alert("CEP não encontrado.");

            return;

        }


        preencherCampo(
            "rua",
            dados.logradouro
        );

        preencherCampo(
            "bairro",
            dados.bairro
        );

        preencherCampo(
            "cidade",
            dados.localidade
        );

        preencherCampo(
            "estado",
            dados.uf
        );


    }catch(erro){

        console.error(
            "Erro ao buscar CEP:",
            erro
        );

        alert(
            "Não foi possível consultar o CEP."
        );

    }

}


// ========================================
// PREENCHER CAMPO
// ========================================

function preencherCampo(id,valor){

    const campo =
        document.getElementById(id);


    if(campo){

        campo.value =
            valor || "";

    }

}


// ========================================
// IDADE / RESPONSÁVEL
// ========================================

function verificarIdade(){

    const campo =
        document.getElementById("nascimento");


    // Página que não possui cadastro
    if(!campo){

        precisaResponsavel = false;

        return;

    }


    if(!campo.value){

        precisaResponsavel = false;

        return;

    }


    const nascimento =
        new Date(campo.value);

    const hoje =
        new Date();


    let idade =
        hoje.getFullYear() -
        nascimento.getFullYear();


    const mes =
        hoje.getMonth() -
        nascimento.getMonth();


    if(
        mes < 0 ||
        (
            mes === 0 &&
            hoje.getDate() < nascimento.getDate()
        )
    ){

        idade--;

    }


    precisaResponsavel =
        idade < 18;

}


// ========================================
// ALERGIA
// ========================================

function mostrarAlergia(){

    const campo =
        document.getElementById(
            "alergia_medicamento"
        );


    const div =
        document.getElementById(
            "divDescricaoAlergia"
        );


    // Página que não possui esses campos
    if(!campo || !div){

        return;

    }


    if(campo.value === "Sim"){

        div.style.display = "block";

    }else{

        div.style.display = "none";


        const descricao =
            document.getElementById(
                "descricao_alergia"
            );


        if(descricao){

            descricao.value = "";

        }

    }

}


// ========================================
// ESTUDO
// ========================================

function mostrarEstudo(){

    const campo =
        document.getElementById("estuda");

    const div =
        document.getElementById("campo_estudo");


    // IMPORTANTE:
    // O wizard.js é carregado em todas as páginas.
    // Se não estivermos no cadastro, esses elementos
    // não existem e a função simplesmente termina.

    if(!campo || !div){

        return;

    }


    const valor =
        campo.value;


    div.style.display =
        valor === "Sim"
            ? "block"
            : "none";

}


// ========================================
// PROFISSÃO
// ========================================

function mostrarProfissao(){

    const campo =
        document.getElementById("trabalha");

    const div =
        document.getElementById("campo_profissao");


    if(!campo || !div){

        return;

    }


    const valor =
        campo.value;


    div.style.display =
        valor === "Sim"
            ? "block"
            : "none";

}


// ========================================
// EXPERIÊNCIA
// ========================================

function mostrarExperiencia(){

    const campo =
        document.getElementById(
            "experiencia_banda"
        );

    const div =
        document.getElementById(
            "campo_experiencia"
        );


    if(!campo || !div){

        return;

    }


    const valor =
        campo.value;


    div.style.display =
        valor === "Sim"
            ? "block"
            : "none";

}


// ========================================
// RESUMO
// ========================================

function montarResumo(){

    const resumo =
        document.getElementById(
            "resumoCadastro"
        );


    if(!resumo){

        return;

    }


    const formulario =
        document.querySelector("form");


    if(!formulario){

        return;

    }


    let html = "";


    const dados =
        new FormData(formulario);


    dados.forEach((valor,campo)=>{

        // FormData pode conter valores que não sejam strings
        const texto =
            String(valor);


        if(texto.trim() !== ""){

            html +=
                `
                <p>
                    <strong>${campo}:</strong>
                    ${texto}
                </p>
                `;

        }

    });


    resumo.innerHTML =
        html;

}


// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener(
    "DOMContentLoaded",
    ()=>{

        /*
         * O wizard.js está no base_admin.html e,
         * portanto, é carregado em TODAS as páginas
         * administrativas.
         *
         * Primeiro verificamos se a página realmente
         * possui elementos do wizard.
         */

        const possuiWizard =
            document.querySelector(".etapa") ||
            document.getElementById("estuda") ||
            document.getElementById("trabalha") ||
            document.getElementById("experiencia_banda");


        /*
         * Mesmo sem wizard, as funções individuais
         * abaixo são seguras porque verificam se
         * seus elementos existem.
         */

        mostrarEtapa();

        mostrarAlergia();

        mostrarEstudo();

        mostrarProfissao();

        mostrarExperiencia();


        /*
         * A variável é mantida apenas para deixar
         * explícita a intenção da inicialização.
         * Não executamos nenhuma lógica adicional
         * em páginas que não possuem o wizard.
         */

        if(!possuiWizard){

            return;

        }

    }
);