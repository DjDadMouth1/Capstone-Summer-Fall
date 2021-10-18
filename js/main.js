
//const downloadFile = "./sample.csv"
const downloadFile = "./result.txt"

$(".run-frictionless").click(function (e) { 
    console.log("runing!!!")
    $(".download").append(`
    <a href="${downloadFile}" download>
        <div class="download-btn">
            Download File
            <i class="fas fa-download"></i>
        </div>
    </a>
    `);
});