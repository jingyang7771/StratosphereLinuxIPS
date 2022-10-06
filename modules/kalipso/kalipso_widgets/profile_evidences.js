const { redis, blessed, blessed_contrib, async } = require("./libraries.js");
const table = require("../lib_widgets/table.js")

class ProfileEvidences extends table.TableClass{

    constructor(grid, redis_database,screen, characteristics){
        super(grid, redis_database, screen, characteristics)
    }

    /*Set evidence for all the timewindows in profile.*/
    setEvidencesInProfile(ip){
        try{
            this.widget.setLabel('profile_'+ip+' Evidences')
            this.redis_database.getAllProfileEvidences(ip).then(all_profile_evidences=>{
                var evidence_data = [];
                if(all_profile_evidences==null){this.setData(['twid','evidences'], evidence_data); this.screen.render()}
                else{
                    var temp_dict = Object.keys(all_profile_evidences)
                    temp_dict.sort(function(a,b){return(Number(a.match(/(\d+)/g)[0]) - Number((b.match(/(\d+)/g)[0])))});

                    async.forEach(temp_dict,(twid, callback)=>{
                    var tw_evidences_json = JSON.parse(all_profile_evidences[twid]);
                        async.forEachOf(Object.entries(tw_evidences_json),([key, evidence], index)=>{
                            var row = []
                            if(index==0){row.push(twid)}
                            else{row.push('')}
                            var evidence_dict = JSON.parse(evidence)
                            var evidence_final = evidence_dict["description"]+'\n'

                            row.push(evidence_final);
                            evidence_data.push(row)
                        })
                    callback()
                    },(err)=>{
                        if(err){console.log('Cannot set evidence in "z" hotkey, check setEvidenceInProfile() in kalipso_table.js. Error: ',err)}
                        else{
                            this.setData(['timewindow','evidence'],evidence_data);
                            this.screen.render();
                        }
                    });
                }
            })
        }
        catch(err){console.log('Check setEvidenceInProfile() in kalipso_table.js. Error: ',err)}
    }

}



module.exports = {ProfileEvidencesClass: ProfileEvidences};
