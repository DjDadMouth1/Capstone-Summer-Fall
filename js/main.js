
//const downloadFile = "./sample.csv"
const downloadFile = "./result.txt"
//const downloadFile = "";

$(".run-frictionless").click(function (e) { 
    console.log("runing!!!")
    if(downloadFile){
        $(".download").append(`
        <a href="${downloadFile}" download>
            <div class="download-btn">
                Download File
                <i class="fas fa-download"></i>
            </div>
        </a>
        `);
    }
    
});