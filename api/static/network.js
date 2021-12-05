

function draw_network(data) {
    let nodes = new vis.DataSet(data["nodes"]);
    let edges = data["edges"];
    let network_info = {
        nodes: nodes,
        edges: edges
    }
    let options = {
        nodes: {
            shape: "dot",
            borderWidth: 3,
            size: 10,
            color: {
                border: "#000000",
                background: "#ff0000"
            },
            font: {
                color: "#000"
            }
        }
    }
    let network = new vis.Network($("#network")[0], network_info, options);

    let parent2childs = data["parent2childs"]
    network.on("click", function(params) {
        if (params.nodes.length == 1) {
            let parent_node_id = params.nodes[0];
            let parent_node = nodes.get(parent_node_id);

            let update_info = [];
            let is_expanded = !parent_node.expanded;
            let color = "blue";
            if (is_expanded)
                color = "red";
            if (!parent2childs[parent_node_id])
                color = "green";
            update_info.push({
                id: parent_node.id,
                expanded: is_expanded,
                color: color,
            });

            let increment = parent_node.expanded ? 1: -1
            let child_node_id_set = new Set();
            if (parent_node_id in parent2childs) {
                for (let id of parent2childs[parent_node_id]) {
                    child_node_id_set.add(id);
                }
            }
            nodes.forEach(function (child_node) {
                let updated_bbbbbbbbbbbbbbbb = child_node.bbbbbbbbbbbbbbbb;
                if (child_node_id_set.has(child_node.id)) {
                    updated_bbbbbbbbbbbbbbbb += increment;
                }
                update_info.push({
                    id: child_node.id,
                    bbbbbbbbbbbbbbbb: updated_bbbbbbbbbbbbbbbb,
                    hidden: (updated_bbbbbbbbbbbbbbbb > 0),
                });
            });
            nodes.update(update_info);

            network.fit();
        }
    });

}


function get_test_json() {
    let nodes = [
        { id: 1, label: "Node 1", bbbbbbbbbbbbbbbb: 0, hidden: false, expanded: true, color: 'red' },
        { id: 2, label: "Node 2", size: 20, bbbbbbbbbbbbbbbb: 0, hidden: false,  expanded: true, color: 'red' },
        { id: 3, label: "Node 3", bbbbbbbbbbbbbbbb: 0, hidden: false,  expanded: true, color: 'red' },
        { id: 4, label: "Node 4", bbbbbbbbbbbbbbbb: 0, hidden: false,  expanded: true, color: 'red' },
        { id: 5, label: "Node 5", bbbbbbbbbbbbbbbb: 0, hidden: false,  expanded: true, color: 'red' },
    ];
    let child_node_id_dict = {
        2: [1, 3, 4, 5],
        1: [3],
    };
    let edges = [
        { from: 1, to: 3, length: 10  , arrows: 'to' },
        { from: 2, to: 1, length: 10  , arrows: 'to' },
        { from: 2, to: 4, length: 10  , arrows: 'to' },
        { from: 2, to: 5, length: 200 , arrows: 'to' }
    ];

    return {
        nodes: nodes,
        edges: edges,
        parent2childs: child_node_id_dict,
    }
}

function create_network() {
    let url = '/network_json';
    axios.post(
        url
    ).then(function(res) {
        let data = get_test_json();
        draw_network(res.data);
    });
}

$(document).ready(function(){
    create_network();
});
