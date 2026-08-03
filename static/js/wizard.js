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


    const progresso = ((etapaAtual - 1) / (totalEtapas - 1)) * 100;


    barra.style.width = progresso + "%";

}



// ========================================
// BOTÕES
// ========================================

function atualizarBotoes(){

    const anterior = document.getElementById("btnAnterior");

    const proximo = document.getElementById("btnProximo");


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


    const etapas = document.querySelectorAll(".etapa");


    const etapa = etapas[etapaAtual - 1];


    if(!etapa){

        return true;

    }


    const campos =
    etapa.querySelectorAll(
        "input[required], select[required], textarea[required]"
    );



    for(let campo of campos){


        if(
            campo.value.trim() === "" ||
            campo.value === "Selecione"
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


    // Antes de sair da etapa 5 verifica novamente a idade
    if(etapaAtual === 5){

        verificarIdade();

    }


    if(!validarEtapa()){

        return;

    }



    if(etapaAtual < totalEtapas){


        etapaAtual++;


        // pula responsável somente se tiver certeza que é maior

        if(
            etapaAtual === 6 &&
            precisaResponsavel === false
        ){

            etapaAtual = 7;

        }


        mostrarEtapa();


    }else{


        document.querySelector("form").submit();


    }

}




function voltarEtapa(){


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




function irParaEtapa(numero){


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


    let valor = campo.value.replace(/\D/g,'');



    if(valor.length > 11){

        valor = valor.substring(0,11);

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


    let valor =
    campo.value.replace(/\D/g,'');



    if(valor.length > 11){

        valor = valor.substring(0,11);

    }



    if(valor.length > 9){

        valor =
        valor.substring(0,3)+"."+
        valor.substring(3,6)+"."+
        valor.substring(6,9)+"-"+
        valor.substring(9);


    }
    else if(valor.length > 6){

        valor =
        valor.substring(0,3)+"."+
        valor.substring(3,6)+"."+
        valor.substring(6);


    }
    else if(valor.length > 3){

        valor =
        valor.substring(0,3)+"."+
        valor.substring(3);

    }



    campo.value = valor;


}



// ========================================
// MÁSCARA CEP
// ========================================

function formatarCEP(campo){


    let valor =
    campo.value.replace(/\D/g,'');



    if(valor.length > 8){

        valor = valor.substring(0,8);

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


    const campo = document.getElementById("cep");


    if(!campo){

        return;

    }


    let cep =
    campo.value.replace(/\D/g,'');



    if(cep.length !== 8){

        return;

    }



    const resposta =
    await fetch(
        "https://viacep.com.br/ws/"+cep+"/json/"
    );


    const dados =
    await resposta.json();



    if(dados.erro){

        alert("CEP não encontrado.");

        return;

    }



    preencherCampo("rua",dados.logradouro);
    preencherCampo("bairro",dados.bairro);
    preencherCampo("cidade",dados.localidade);
    preencherCampo("estado",dados.uf);


}



function preencherCampo(id,valor){


    const campo =
    document.getElementById(id);


    if(campo){

        campo.value = valor || "";

    }

}



// ========================================
// IDADE / RESPONSÁVEL
// ========================================

function verificarIdade(){

    console.log("FUNÇÃO VERIFICAR IDADE CHAMADA");


    const campo = document.getElementById("nascimento");


    if(!campo || !campo.value){

        console.log("Sem data");

        precisaResponsavel = false;

        return;

    }


    console.log("Data recebida:", campo.value);


    const nascimento = new Date(campo.value);

    const hoje = new Date();


    let idade = hoje.getFullYear() - nascimento.getFullYear();


    const mes = hoje.getMonth() - nascimento.getMonth();


    if(
        mes < 0 ||
        (
            mes === 0 &&
            hoje.getDate() < nascimento.getDate()
        )
    ){

        idade--;

    }


    precisaResponsavel = idade < 18;


    console.log(
        "IDADE CALCULADA:",
        idade,
        "PRECISA RESPONSÁVEL:",
        precisaResponsavel
    );

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


    if(!campo || !div){

        return;

    }



    if(campo.value === "Sim"){


        div.style.display="block";


    }else{


        div.style.display="none";


        const descricao =
        document.getElementById(
            "descricao_alergia"
        );


        if(descricao){

            descricao.value="";

        }

    }

}

// ===============================
// ESTUDO
// ===============================

function mostrarEstudo(){

    const valor = document.getElementById("estuda").value;

    document.getElementById("campo_estudo").style.display =
        valor === "Sim" ? "block" : "none";

}



// ===============================
// PROFISSÃO
// ===============================

function mostrarProfissao(){

    const valor = document.getElementById("trabalha").value;

    document.getElementById("campo_profissao").style.display =
        valor === "Sim" ? "block" : "none";

}



// ===============================
// EXPERIÊNCIA
// ===============================

function mostrarExperiencia(){

    const valor = document.getElementById("experiencia_banda").value;

    document.getElementById("campo_experiencia").style.display =
        valor === "Sim" ? "block" : "none";

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



    let html="";


    const dados =
    new FormData(
        document.querySelector("form")
    );



    dados.forEach((valor,campo)=>{


        if(valor.trim() !== ""){


            html +=
            `
            <p>
            <strong>${campo}:</strong>
            ${valor}
            </p>
            `;


        }


    });



    resumo.innerHTML = html;


}


// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener(
"DOMContentLoaded",
()=>{

    mostrarEtapa();

    mostrarAlergia();

    mostrarEstudo();

    mostrarProfissao();

    mostrarExperiencia();

});